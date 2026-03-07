#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void print_bar(int percent, char* prefix) {
    int width = 5;
    int filled = (percent * width) / 100;
    
    if (filled > width) filled = width;
    if (filled < 0) filled = 0;

    printf("%s [", prefix);
    for (int i = 0; i < width; i++) {
        if (i < filled) printf("█");
        else printf("░");
    }
    printf("]\n");
}

void get_ram() {
    FILE *fp = fopen("/proc/meminfo", "r");
    if (!fp) {
        printf("RAM [Error]\n");
        return;
    }
    
    char line[256];
    long total = 0, available = 0;
    
    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, "MemTotal:", 9) == 0) sscanf(line, "MemTotal: %ld kB", &total);
        if (strncmp(line, "MemAvailable:", 13) == 0) sscanf(line, "MemAvailable: %ld kB", &available);
    }
    fclose(fp);
    
    if (total > 0) {
        int percent = ((total - available) * 100) / total;
        print_bar(percent, "RAM");
    } else {
        printf("RAM [Error]\n");
    }
}

void get_cpu() {
    long user1, nice1, system1, idle1, iowait1, irq1, softirq1;
    long user2, nice2, system2, idle2, iowait2, irq2, softirq2;
    
    FILE *fp = fopen("/proc/stat", "r");
    if (!fp) { 
        printf("CPU [Error]\n"); 
        return; 
    }
    fscanf(fp, "cpu %ld %ld %ld %ld %ld %ld %ld", &user1, &nice1, &system1, &idle1, &iowait1, &irq1, &softirq1);
    fclose(fp);

    usleep(100000); 

    fp = fopen("/proc/stat", "r");
    if (!fp) { 
        printf("CPU [Error]\n"); 
        return; 
    }
    fscanf(fp, "cpu %ld %ld %ld %ld %ld %ld %ld", &user2, &nice2, &system2, &idle2, &iowait2, &irq2, &softirq2);
    fclose(fp);

    long idle_time = (idle2 + iowait2) - (idle1 + iowait1);
    long total_time = idle_time + (user2 + nice2 + system2 + irq2 + softirq2) - (user1 + nice1 + system1 + irq1 + softirq1);

    int percent = 0;
    if (total_time > 0) {
        percent = ((total_time - idle_time) * 100) / total_time;
    }
    print_bar(percent, "CPU");
}

void get_gpu() {
    FILE *fp = popen("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits", "r");
    if (!fp) {
        printf("GPU [Error]\n");
        return;
    }
    
    int usage = 0;
    if (fscanf(fp, "%d", &usage) == 1) {
        print_bar(usage, "GPU");
    } else {
        printf("GPU [Error]\n");
    }
    pclose(fp);
}

void get_battery() {
    FILE *f_cap = fopen("/sys/class/power_supply/BAT0/capacity", "r");
    FILE *f_stat = fopen("/sys/class/power_supply/BAT0/status", "r");
    
    if (!f_cap || !f_stat) {
        printf("BAT --%%\n");
        if (f_cap) fclose(f_cap);
        if (f_stat) fclose(f_stat);
        return;
    }
    
    int capacity = 0;
    fscanf(f_cap, "%d", &capacity);
    fclose(f_cap);
    
    char status[32];
    fscanf(f_stat, "%31s", status);
    fclose(f_stat);
    
    if (strcmp(status, "Charging") == 0) {
        printf("⚡ %d%%\n", capacity);
    } else {
        printf("BAT %d%%\n", capacity);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    
    if (strcmp(argv[1], "cpu") == 0) get_cpu();
    else if (strcmp(argv[1], "ram") == 0) get_ram();
    else if (strcmp(argv[1], "gpu") == 0) get_gpu();
    else if (strcmp(argv[1], "bat") == 0) get_battery();
    
    return 0;
}