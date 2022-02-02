#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <unistd.h>
#include <fcntl.h>
#include <ctype.h>
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES2/gl2.h>
#include <gbm.h>

static char* read_file(const char* path)
{
    FILE* fd = fopen(path, "r");
    if(!fd)
    {
        fprintf(stderr, "failed to open %s\n", path);
        exit(1);
    }
    fseek(fd, 0, SEEK_END);
    off_t sz = ftell(fd);
    fseek(fd, 0, SEEK_SET);
    char* out = malloc(sz+1);
    if(fread(out, sz, 1, fd) != 1)
    {
        fprintf(stderr, "failed to read %s\n", path);
        fclose(fd);
        exit(1);
    }
    fclose(fd);
    out[sz] = 0;
    return out;
}

static void print_compilation_error(GLint which)
{
    GLint sz;
    glGetShaderiv(which, GL_INFO_LOG_LENGTH, &sz);
	if(which > 0)
    {
		char data[sz+1];
		glGetShaderInfoLog(which, sz, NULL, data);
        data[sz] = 0;
        int q = 1;
        for(size_t i = 0; i < sz && q; i++)
            if(!isspace(data[sz]))
                q = 0;
        if(!q)
        {
            printf("\n*** COMPILATION ERROR ***\n");
		    printf("%s\n", data);
            printf("\n*************************\n");
        }
	}
}

int main(int argc, const char** argv)
{
    if(argc != 3)
    {
        fprintf(stderr, "usage: victim <vertex.glsl> <fragment.glsl>\n");
        return 1;
    }
    int fd = open("/dev/dri/renderD128", O_RDWR);
    struct gbm_device* dev = gbm_create_device(fd);
    EGLDisplay disp = eglGetPlatformDisplay(EGL_PLATFORM_GBM_MESA, dev, NULL);
    eglInitialize(disp, NULL, NULL);
    const EGLint attribs[] = {
        EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
        EGL_NONE,
    };
    EGLConfig cfg;
    EGLint ncfg;
    eglChooseConfig(disp, attribs, &cfg, 1, &ncfg);
    eglBindAPI(EGL_OPENGL_ES_API);
    const EGLint attrs[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE,
    };
    EGLContext ctxt = eglCreateContext(disp, cfg, EGL_NO_CONTEXT, attrs);
    eglMakeCurrent(disp, EGL_NO_SURFACE, EGL_NO_SURFACE, ctxt);
    GLuint fb;
    glGenFramebuffers(1, &fb);
    glBindFramebuffer(GL_FRAMEBUFFER, fb);
    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 1, 1, 0, GL_RGBA, GL_UNSIGNED_BYTE, NULL);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);
    glViewport(0, 0, 1, 1);
    GLuint vert = glCreateShader(GL_VERTEX_SHADER);
    const char* src = read_file(argv[1]);
    glShaderSource(vert, 1, &src, NULL);
    glCompileShader(vert);
    print_compilation_error(vert);
    GLuint frag = glCreateShader(GL_FRAGMENT_SHADER);
    src = read_file(argv[2]);
    glShaderSource(frag, 1, &src, NULL);
    glCompileShader(frag);
    print_compilation_error(frag);
    GLuint prog = glCreateProgram();
    glAttachShader(prog, vert);
    glAttachShader(prog, frag);
    glLinkProgram(prog);
    glUseProgram(prog);
    GLint nUniforms = -1;
    glGetProgramiv(prog, GL_ACTIVE_UNIFORMS, &nUniforms);
    printf("nUniforms = %d\n", nUniforms);
    for(GLint i = 0; i < nUniforms; i++)
    {
        GLint size = -1;
        GLenum type = -1;
        GLint namelen = -1;
        char name[256] = {0};
        glGetActiveUniform(prog, i, 255, &namelen, &size, &type, name);
        printf("uniform %s type 0x%x size %d\n", name, (unsigned)type, size);
    }
    GLint nAttributes = -1;
    glGetProgramiv(prog, GL_ACTIVE_ATTRIBUTES, &nAttributes);
    for(GLint i = 0; i < nAttributes; i++)
    {
        GLint size = -1;
        GLenum type = -1;
        GLint namelen = -1;
        char name[256] = {0};
        glGetActiveAttrib(prog, i, 255, &namelen, &size, &type, name);
        printf("attribute %s type 0x%x size %d\n", name, (unsigned)type, size);
    }
    glClearColor(0.0, 0.0, 0.0, 1.0);
    glClear(GL_COLOR_BUFFER_BIT);
    glDrawArrays(GL_TRIANGLES, 0, 1);
}
