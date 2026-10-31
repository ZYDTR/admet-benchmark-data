/* Redirect only optional writes naming this process's threads to /dev/null.
 * Keep all filesystem permissions and Landlock rules unchanged.
 * All other file operations and all CUDA/model computation call the originals.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
static int is_thread_comm(const char *p) {
    char prefix[80]; const char *q;
    if (!p) return 0;
    if (!strncmp(p,"/proc/self/task/",16)) q=p+16;
    else {
        snprintf(prefix,sizeof(prefix),"/proc/%ld/task/",(long)getpid());
        size_t n=strlen(prefix); if (strncmp(p,prefix,n)) return 0; q=p+n;
    }
    if (*q<'0'||*q>'9') return 0;
    while (*q>='0'&&*q<='9') ++q;
    return !strcmp(q,"/comm");
}
int pthread_setname_np(pthread_t t,const char *n) {(void)t;(void)n;return 0;}
FILE *fopen(const char *p,const char *m) {
    FILE *(*fn)(const char*,const char*)=dlsym(RTLD_NEXT,"fopen");
    if (is_thread_comm(p)&&strpbrk(m,"wa+")) return fn("/dev/null",strchr(m,'+')?"a+":"a");
    return fn(p,m);
}
FILE *fopen64(const char *p,const char *m) {
    FILE *(*fn)(const char*,const char*)=dlsym(RTLD_NEXT,"fopen64");
    if (is_thread_comm(p)&&strpbrk(m,"wa+")) return fn("/dev/null",strchr(m,'+')?"a+":"a");
    return fn(p,m);
}
#define OPEN_WRAPPER(NAME) \
int NAME(const char *p,int flags,...) { \
    mode_t mode=0; if ((flags&O_CREAT)||((flags&O_TMPFILE)==O_TMPFILE)) {va_list v;va_start(v,flags);mode=va_arg(v,mode_t);va_end(v);} \
    int (*fn)(const char*,int,...)=dlsym(RTLD_NEXT,#NAME); \
    if (is_thread_comm(p)&&(flags&(O_WRONLY|O_RDWR))) return fn("/dev/null",flags&~(O_CREAT|O_TRUNC|O_EXCL),0); \
    return fn(p,flags,mode); \
}
OPEN_WRAPPER(open)
OPEN_WRAPPER(open64)
#define OPENAT_WRAPPER(NAME) \
int NAME(int dir,const char *p,int flags,...) { \
    mode_t mode=0; if ((flags&O_CREAT)||((flags&O_TMPFILE)==O_TMPFILE)) {va_list v;va_start(v,flags);mode=va_arg(v,mode_t);va_end(v);} \
    int (*fn)(int,const char*,int,...)=dlsym(RTLD_NEXT,#NAME); \
    if (is_thread_comm(p)&&(flags&(O_WRONLY|O_RDWR))) return fn(AT_FDCWD,"/dev/null",flags&~(O_CREAT|O_TRUNC|O_EXCL),0); \
    return fn(dir,p,flags,mode); \
}
OPENAT_WRAPPER(openat)
OPENAT_WRAPPER(openat64)
