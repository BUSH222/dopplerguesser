#include <iostream>
#include <complex>
#include <vector>
#include <random>
#include <thread>
#include <chrono>
#include <cmath>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <atomic>
#include <string>
#include <sstream>

std::atomic<double> current_f_s(10000.0);
std::atomic<float> current_w_s(0.02f);
std::atomic<double> current_samp_rate(192000.0);
std::atomic<bool> restart_connection(false);
std::atomic<bool> trigger_sweep(false);
std::atomic<bool> stop_sweep(false);

void input_thread() {
    std::string line;
    while (std::getline(std::cin, line)) {
        std::istringstream iss(line);
        std::string command;
        iss >> command;

        if (command == "f") {
            double freq;
            if (iss >> freq) {
                current_f_s.store(freq);
                std::cout << "Frequency set to " << freq << " Hz" << std::endl;

            }
        } else if (command == "a") {
            float amp;
            if (iss >> amp) {
                current_w_s.store(amp);
                std::cout << "Amplitude set to " << amp << std::endl;
            }
        } else if (command == "s") {
            double sr;
            if (iss >> sr) {
                current_samp_rate.store(sr * 1000000.0);
                std::cout << "Sample rate set to " << current_samp_rate.load() << " Hz" << std::endl;
                restart_connection.store(true);
            }
        } else if (command == "sweep") {
            trigger_sweep.store(true);
            std::cout << "Sweep triggered." << std::endl;
        } else if (command == "stop") {
            stop_sweep.store(true);
            std::cout << "Sweep stop triggered." << std::endl;
        } else {
            std::cout << "Unknown command: " << command << std::endl;
        }
    }
}

int main() {
    const float w_n = 0.4f;
    const int port = 1234;

    const int buffer_size = 4096;
    std::vector<std::complex<float>> buffer(buffer_size);

    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> noise_dist(0.0f, w_n);

    int server_fd;
    struct sockaddr_in address;
    int opt = 1;
    socklen_t addrlen = sizeof(address);

    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        std::cerr << "Socket creation failed" << std::endl;
        return 1;
    }

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        std::cerr << "Setsockopt failed" << std::endl;
        return 1;
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Bind failed" << std::endl;
        return 1;
    }

    if (listen(server_fd, 3) < 0) {
        std::cerr << "Listen failed" << std::endl;
        return 1;
    }

    std::thread input_thr(input_thread);
    input_thr.detach();

    while (true) {
        int client_socket;
        std::cout << "Waiting for connection on port " << port << "..." << std::endl;
        if ((client_socket = accept(server_fd, (struct sockaddr*)&address, &addrlen)) < 0) {
            std::cerr << "Accept failed" << std::endl;
            return 1;
        }

        std::cout << "Client connected. Streaming cf32 samples... Current Sample Rate: " << current_samp_rate.load() << " Hz" << std::endl;

        double current_phase = 0.0;
        bool is_sweeping = false;
        double sweep_t = 0.0;
        restart_connection.store(false);

        auto time_start = std::chrono::steady_clock::now();
        uint64_t samples_sent = 0;

        while (!restart_connection.load()) {
            double rate = current_samp_rate.load();
            float amp = current_w_s.load();
            const double dt = 1.0 / rate;

            // Check triggers
            if (trigger_sweep.load()) {
                is_sweeping = true;
                sweep_t = 0.0;
                trigger_sweep.store(false);
            }
            if (stop_sweep.load()) {
                is_sweeping = false;
                stop_sweep.store(false);
            }

            for (int i = 0; i < buffer_size; ++i) {
                double freq;
                if (is_sweeping) {
                    freq = -63333.0 * (sweep_t - 300.0) / std::sqrt((sweep_t - 300.0)*(sweep_t - 300.0) + 175.0*175.0);
                    sweep_t += dt;
                    if (sweep_t >= 600.0) {
                        is_sweeping = false;
                        std::cout << "Sweep finished (600 seconds reached)." << std::endl;
                    }
                } else {
                    freq = current_f_s.load();
                }

                double phase_increment = 2.0 * M_PI * freq * dt;

                std::complex<float> signal(amp * std::cos(current_phase), amp * std::sin(current_phase));
                std::complex<float> noise(noise_dist(gen), noise_dist(gen));
                
                buffer[i] = signal + noise;
                
                current_phase += phase_increment;
                if (current_phase > 2.0 * M_PI) {
                    current_phase -= 2.0 * M_PI;
                } else if (current_phase < -2.0 * M_PI) {
                    current_phase += 2.0 * M_PI;
                }
            }

            ssize_t bytes_sent = send(client_socket, buffer.data(), buffer_size * sizeof(std::complex<float>), MSG_NOSIGNAL);
            
            if (bytes_sent < 0) {
                std::cerr << "Client disconnected or send failed." << std::endl;
                break;
            }

            samples_sent += buffer_size;

            auto time_now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::duration<double>>(time_now - time_start).count();
            double expected_time = static_cast<double>(samples_sent) / rate;
            
            if (expected_time > elapsed) {
                std::this_thread::sleep_for(std::chrono::duration<double>(expected_time - elapsed));
            }
        }
        
        close(client_socket);
        if (restart_connection.load()) {
            std::cout << "Connection dropped due to sample rate change." << std::endl;
        }
    }

    close(server_fd);
    return 0;
}
