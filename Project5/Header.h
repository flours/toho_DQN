#pragma once

#include <windows.h>
#include<stdio.h>


#ifdef CAP_EXPORTS
#define CAP_API __declspec(dllexport)
#else
#define CAP_API __declspec(dllimport)
#endif

extern "C" CAP_API void hello();
extern "C" CAP_API void capture_desktop(unsigned char* capture_img);
extern "C" CAP_API void capture_foreground(unsigned char* capture_img);
extern "C" CAP_API void capture_life_board(unsigned char* capture_img);
extern "C" CAP_API void capture_life_board(unsigned char* capture_img);
extern "C" CAP_API void step(int action, unsigned char* capture_img, int* reward, int* life, int* done);
extern "C" CAP_API int mytemplatematch(unsigned char* capture_img, int* loc_x, int* loc_y);
extern "C" CAP_API int templatematch(unsigned char* capture_img, int* loc_x, int* loc_y);
