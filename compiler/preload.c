#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <string.h>
#include <signal.h>
#include <dirent.h>
#include <errno.h>
#include <drm/drm.h>
#include <drm/radeon_drm.h>

int stat64(const char* path, struct stat64* restrict out)
{
    static int(*real_stat64)(const char*, struct stat64*);
    if(!real_stat64)
        real_stat64 = dlsym(RTLD_NEXT, "stat64");
    if(!strncmp(path, "/sys/", 5) || !strncmp(path, "/dev/dri/", 9))
    {
        memset(out, 0, sizeof(*out));
        if(!strcmp(path, "/dev/dri/card0"))
        {
            out->st_mode = 020660;
            out->st_rdev = 0xe200;
        }
        else if(!strcmp(path, "/dev/dri/renderD128"))
        {
            out->st_mode = 020666;
            out->st_rdev = 0xe280;
        }
        return 0;
    }
    return real_stat64(path, out);
}

int fstat64(int fd, struct stat64* out)
{
    static int(*real_fstat64)(int, struct stat64*);
    if(!real_fstat64)
        real_fstat64 = dlsym(RTLD_NEXT, "fstat64");
    if(fd == 1000000000)
    {
        memset(out, 0, sizeof(*out));
        out->st_mode = 020666;
        out->st_rdev = 0xe280;
        return 0;
    }
    return real_fstat64(fd, out);
}

int readlink(const char* path, char* dst, size_t sz)
{
    static int(*real_readlink)(const char*, char*, size_t);
    if(!real_readlink)
        real_readlink = dlsym(RTLD_NEXT, "readlink");
    if(!strncmp(path, "/sys/", 5))
    {
        if(sz > 5)
            sz = 5;
        sz--;
        memcpy(dst, "/pci", sz);
        dst[sz] = 0;
        return sz + 1;
    }
    return real_readlink(path, dst, sz);
}

char* realpath(const char* path, char* dst)
{
    static char*(*real_realpath)(const char*, char*);
    if(!real_realpath)
        real_realpath = dlsym(RTLD_NEXT, "realpath");
    if(!strncmp(path, "/sys/", 5))
    {
        size_t l = strlen(path) + 1;
        if(!dst)
            dst = malloc(l);
        memcpy(dst, path, l);
        return dst;
    }
    return real_realpath(path, dst);
}

FILE* fopen64(const char* path, const char* mode)
{
    static FILE*(*real_fopen64)(const char*, const char*);
    if(!real_fopen64)
        real_fopen64 = dlsym(RTLD_NEXT, "fopen64");
    if(!strncmp(path, "/sys/", 5))
    {
        const char* which = strrchr(path, '/');
        FILE* f = fmemopen(NULL, 4096, "r+");
        if(!strcmp(which, "/uevent"))
            fprintf(f, "PCI_SLOT_NAME=0000:00:00.0\n");
        else if(!strcmp(which, "/vendor"))
            fprintf(f, "0x1002\n");
        else if(!strcmp(which, "/device"))
            fprintf(f, "0x665c\n");
        else if(!strcmp(which, "/subsystem_vendor"))
            fprintf(f, "0x1043\n");
        else if(!strcmp(which, "/subsystem_device"))
            fprintf(f, "0x0452\n");
        else
            __builtin_trap();
        fflush(f);
        fseek(f, 0, SEEK_SET);
        return f;
    }
    return real_fopen64(path, mode);
}

drm_version_t* drmGetVersion(int fd)
{
    drm_version_t* ans = calloc(1, sizeof(*ans));
    ans->version_major = 2;
    ans->version_minor = 12;
    return ans;
}

int drmIoctl(int fd, unsigned long request, void* uap)
{
    if(request == DRM_IOCTL_GEM_CLOSE)
        return 0;
    __builtin_trap();
    return -1;
}

int drmCommandWriteRead(int fd, unsigned long drmCommandIndex, void* data, unsigned long size)
{
    if(drmCommandIndex == DRM_RADEON_INFO)
    {
        struct drm_radeon_info* out = data;
        if(out->request == RADEON_INFO_DEVICE_ID)
            *(uint32_t*)out->value = 0x665c;
        else
            *(uint32_t*)out->value = 1;
        return 0;
    }
    else if(drmCommandIndex == DRM_RADEON_GEM_USERPTR)
        return 0;
    else if(drmCommandIndex == DRM_RADEON_GEM_INFO)
        return 0;
    else if(drmCommandIndex == DRM_RADEON_GEM_CREATE)
    {
        static int handle = 0;
        struct drm_radeon_gem_create* out = data;
        out->handle = ++handle;
        return 0;
    }
    else if(drmCommandIndex == DRM_RADEON_GEM_MMAP)
    {
        struct drm_radeon_gem_mmap* out = data;
        out->addr_ptr = 0;
        return 0;
    }
    else if(drmCommandIndex == DRM_RADEON_GEM_SET_TILING)
        return 0;
    else if(drmCommandIndex == DRM_RADEON_CS)
        return 0;
    __builtin_trap();
    return -1;
}

int drmCommandWrite(int fd, unsigned long drmCommandIndex, void* data, unsigned long size)
{
    if(drmCommandIndex == DRM_RADEON_GEM_WAIT_IDLE)
        return 0;
    __builtin_trap();
    return -1;
}

void* mmap64(void* addr, size_t sz, int prot, int flags, int fd, off_t offset)
{
    static void*(*real_mmap64)(void*, size_t, int, int, int, off_t);
    if(!real_mmap64)
        real_mmap64 = dlsym(RTLD_NEXT, "mmap64");
    if(fd == 1000000000)
    {
        fd = -1;
        flags |= MAP_ANONYMOUS;
    }
    void* ans = real_mmap64(addr, sz, prot, flags, fd, offset);
    return ans;
}

int drmGetCap(int fd, uint64_t capability, uint64_t* value)
{
    errno = EINVAL;
    return -1;
}

int drmPrimeHandleToFD(int fd, uint32_t handle, uint32_t flags, int* prime_fd)
{
    *prime_fd = fd;
    return 0;
}

int __fprintf_chk(FILE* f, int flags, const char* p, ...)
{
    va_list l;
    va_start(l, p);
    if(!strcmp(p, "%*s"))
    {
        int sz = va_arg(l, int);
        const char* s = va_arg(l, const char*);
        fwrite(s, sz, 1, f);
        return sz;
    }
    return vfprintf(f, p, l);
}

int open(const char* path, int flags, ...)
{
    va_list va;
    va_start(va, flags);
    mode_t mode = va_arg(va, int);
    va_end(va);
    if(!strncmp(path, "/dev/dri/", 9))
        return 1000000000;
    static int(*real_open)(const char*, int, ...);
    if(!real_open)
        real_open = dlsym(RTLD_NEXT, "open64");
    return real_open(path, flags, mode);
}

int open64(const char* path, int flags, ...)
{
    va_list va;
    va_start(va, flags);
    mode_t mode = va_arg(va, int);
    va_end(va);
    return open(path, flags, mode);
}

int close(int fd)
{
    static int(*real_close)(int);
    if(!real_close)
        real_close = dlsym(RTLD_NEXT, "close");
    if(fd == 1000000000)
        return 0;
    return real_close(fd);
}

int fcntl64(int fd, int cmd, ...)
{
    va_list va;
    va_start(va, cmd);
    long arg = va_arg(va, long);
    va_end(va);
    static int(*real_fcntl64)(int, int, ...);
    if(!real_fcntl64)
        real_fcntl64 = dlsym(RTLD_NEXT, "fcntl64");
    if(fd == 1000000000)
    {
        if(cmd == F_DUPFD_CLOEXEC)
            return fd;
    }
    return real_fcntl64(fd, cmd, arg);
}

static int fake_dir;

DIR* opendir(const char* path)
{
    static DIR*(*real_opendir)(const char*);
    if(!real_opendir)
        real_opendir = dlsym(RTLD_NEXT, "opendir");
    if(!strcmp(path, "/dev/dri"))
    {
        fake_dir = 0;
        return (DIR*)1;
    }
    return real_opendir(path);
}

struct dirent64* readdir64(DIR* d)
{
    static struct dirent64*(*real_readdir64)(DIR*);
    if(!real_readdir64)
        real_readdir64 = dlsym(RTLD_NEXT, "readdir64");
    if(d == (DIR*)1)
    {
        static struct dirent64 ans = {.d_name = "renderD128"};
        return fake_dir++ ? NULL : &ans;
    }
    return real_readdir64(d);
}

int closedir(DIR* d)
{
    static int (*real_closedir)(DIR*);
    if(!real_closedir)
        real_closedir = dlsym(RTLD_NEXT, "closedir");
    if(d == (DIR*)1)
        return 0;
    return real_closedir(d);
}
