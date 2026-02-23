import sys
import subprocess
import time
import psutil
import os

def measure_process(command, duration=5):
    start_time = time.time()
    process = subprocess.Popen(command, shell=True)
    
    # Wait for the process to fully initialize
    time.sleep(2) 
    
    p = psutil.Process(process.pid)
    # Include children processes (Flet/Qt might spawn them)
    all_procs = [p] + p.children(recursive=True)
    
    startup_time = time.time() - start_time
    
    mem_samples = []
    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            total_rss = 0
            for proc in [p] + p.children(recursive=True):
                total_rss += proc.memory_info().rss
            mem_samples.append(total_rss / (1024 * 1024)) # MB
            time.sleep(0.5)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break
            
    # Cleanup
    for proc in p.children(recursive=True):
        try:
            proc.terminate()
        except:
            pass
    p.terminate()
    process.wait()
    
    avg_mem = sum(mem_samples) / len(mem_samples) if mem_samples else 0
    max_mem = max(mem_samples) if mem_samples else 0
    
    return startup_time, avg_mem, max_mem

if __name__ == "__main__":
    print("Benchmarking Flet App (main.py)...")
    flet_start, flet_avg, flet_max = measure_process(r".venv\Scripts\python.exe main.py")
    
    time.sleep(2)
    
    print("Benchmarking PySide6 Prototype...")
    proto_start, proto_avg, proto_max = measure_process(r".venv\Scripts\python.exe prototype/main_window.py")
    
    print("\n--- Performance Results ---")
    print(f"{'Metric':<20} | {'Flet':<15} | {'PySide6 Proto':<15} | {'Improvement':<15}")
    print("-" * 75)
    print(f"{'Startup Time (s)':<20} | {flet_start:<15.2f} | {proto_start:<15.2f} | {((flet_start-proto_start)/flet_start)*100:<14.1f}%")
    print(f"{'Avg Memory (MB)':<20} | {flet_avg:<15.2f} | {proto_avg:<15.2f} | {((flet_avg-proto_avg)/flet_avg)*100:<14.1f}%")
    print(f"{'Max Memory (MB)':<20} | {flet_max:<15.2f} | {proto_max:<15.2f} | {((flet_max-proto_max)/flet_max)*100:<14.1f}%")
