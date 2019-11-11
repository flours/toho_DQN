#define _CRT_SECURE_NO_WARNINGS



#include "Header.h"
#include"opencv2/opencv.hpp"
#include<time.h>

#include "Header.h"

HBITMAP CreateBackbuffer(int nWidth, int nHeight);


void my_print(const char* text)
{
	FILE* fp;
	if ((fp = fopen("C:\\anaconda\\myprogram\\debug.txt", "a")) == NULL)
		return;
	fprintf(fp, text);
	fclose(fp);
}


void hello()
{
	printf("aa");
}


void capture_desktop(unsigned char* capture_img)
{
	int s = clock();

	HDC     hdc;
	HWND    hwndDesk;
	RECT    rc;
	BITMAP  bm;
	static HBITMAP hbmp;
	HBITMAP hbmpPrev;

	hwndDesk = GetDesktopWindow();
	GetWindowRect(hwndDesk, &rc);



	hdc = CreateCompatibleDC(NULL);
	hbmp = CreateBackbuffer(rc.right, rc.bottom);


	hbmpPrev = (HBITMAP)SelectObject(hdc, hbmp);

	int s2 = clock();


	BitBlt(hdc, 0, 0, rc.right, rc.bottom, GetWindowDC(hwndDesk), 0, 0, SRCCOPY);


	int s3 = clock();


	GetObject(hbmp, sizeof(BITMAP), &bm);


	memcpy(capture_img ,bm.bmBits,sizeof(char)*1920*1080*3);

	char str[100];
	sprintf(str, "%d\n", clock() - s-(s3-s2));
	my_print(str);

	return;
}


void capture_foreground(unsigned char* capture_img)
{

	HDC     hdc;
	HWND    hwndDesk;
	HWND    hwndFore;
	RECT    rc;
	RECT    rc_fore;
	BITMAP  bm;
	HBITMAP hbmp;
	HBITMAP hbmpPrev;

	hwndDesk = GetDesktopWindow();
	hwndFore = GetForegroundWindow();
	GetWindowRect(hwndDesk, &rc);
	GetWindowRect(hwndFore, &rc_fore);


	hdc = CreateCompatibleDC(NULL);
	hbmp = CreateBackbuffer(384, 448);
	hbmpPrev = (HBITMAP)SelectObject(hdc, hbmp);
	HDC winDC = GetWindowDC(hwndDesk);
	if (winDC == 0) {
		printf("winDC==0!");
		return;
	}
	BitBlt(hdc, 0, 0, 384, 448, winDC, rc_fore.left + 33, rc_fore.top + 42, SRCCOPY);




	GetObject(hbmp, sizeof(BITMAP), &bm);


	memcpy(capture_img, bm.bmBits, sizeof(unsigned char) * 384 * 448 * 3);

	DeleteDC(hdc);
	ReleaseDC(hwndDesk,winDC);
	DeleteObject(hbmp);
	DeleteObject(hbmpPrev);



	return;
}


void capture_life_board(unsigned char* capture_img)
{

	HDC     hdc;
	HWND    hwndDesk;
	HWND    hwndFore;
	RECT    rc;
	RECT    rc_fore;
	BITMAP  bm;
	HBITMAP hbmp;
	HBITMAP hbmpPrev;

	hwndDesk = GetDesktopWindow();
	hwndFore = GetForegroundWindow();
	GetWindowRect(hwndDesk, &rc);
	GetWindowRect(hwndFore, &rc_fore);

	int left_top_x = 497;
	int left_top_y = 149;

	int size_x = 144;
	int size_y = 48;


	hdc = CreateCompatibleDC(NULL);
	hbmp = CreateBackbuffer(size_x, size_y);
	if (GetLastError() != 0)
		printf("error=%d\n", GetLastError());
	hbmpPrev = (HBITMAP)SelectObject(hdc, hbmp);
	HDC winDC = GetWindowDC(hwndDesk);
	if (GetLastError() != 0)
		printf("error=%d\n", GetLastError());
	if (winDC == 0)return;
	if (rc_fore.left + left_top_x >= rc.right || rc_fore.top + left_top_y >= rc.bottom)return;

	BitBlt(hdc, 0, 0, size_x, size_y, winDC, rc_fore.left + left_top_x, rc_fore.top + left_top_y, SRCCOPY);




	GetObject(hbmp, sizeof(BITMAP), &bm);


	memcpy(capture_img, bm.bmBits, sizeof(unsigned char) * size_x * size_y * 3);
	DeleteDC(hdc);
	ReleaseDC(hwndDesk,winDC);
	DeleteObject(hbmp);
	DeleteObject(hbmpPrev);
	if(GetLastError()!=0)
		printf("error=%d\n", GetLastError());


	return;
}

HBITMAP CreateBackbuffer(int nWidth, int nHeight)
{
	LPVOID           lp;
	BITMAPINFO       bmi;
	BITMAPINFOHEADER bmiHeader;

	ZeroMemory(&bmiHeader, sizeof(BITMAPINFOHEADER));
	bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
	bmiHeader.biWidth = nWidth;
	bmiHeader.biHeight = nHeight;
	bmiHeader.biPlanes = 1;
	bmiHeader.biBitCount = 24;

	bmi.bmiHeader = bmiHeader;

	return CreateDIBSection(NULL, (LPBITMAPINFO)& bmi, DIB_RGB_COLORS, &lp, NULL, 0);
}


//ÉeÉìÉvÉåÅ[ÉgÉ}ÉbÉ`ópâÊëú
cv::Mat imgs[9];
cv::Mat mask_imgs[9];
void reset() 
{
	for (int i = 0; i < 9; i++) {
		cv::Mat mask_orig;
		char file[] = " _alpha.png";
		file[0] = i + '1';
		printf("%s", file);
		imgs[i] = cv::imread(file);
		mask_orig= cv::imread(file,cv::IMREAD_UNCHANGED);
		printf("%d,channels=%d",i,mask_orig.channels());
		cv::Mat channels[4];
		cv::split(mask_orig,channels);
		std::vector<cv::Mat> tmp_a;
		tmp_a.push_back(channels[3]);
		tmp_a.push_back(channels[3]);
		tmp_a.push_back(channels[3]);
		cv::merge(tmp_a,mask_imgs[i]);
	}
}



int before_x=0, before_y=0;

int templatematch(unsigned char* capture_img, int* loc_x, int* loc_y) {
	reset();
	cv::Mat img(448, 384, CV_8UC3, capture_img);
	cv::Mat result_img;
	double maxVal=-9999;

	
	if (before_x!=0) {
		int x = before_x;
		int y = before_y;
		if (before_x < 0)x = 0;
		if (before_y < 0)y = 0;
		if (before_x > 384-101)x = 384-101;
		if (before_y > 448-151)y = 448-151;

		cv::Rect roi(cv::Point(x,y), cv::Size(100, 150));
		img = img(roi);
		before_x = x;
		before_y = y;

	}
	for (int i = 1; i < 9; i++) {
		double Val = 0;
		cv::matchTemplate(img, imgs[i], result_img, cv::TM_CCORR_NORMED,mask_imgs[i]);
		cv::Point max_pt;
		cv::minMaxLoc(result_img, NULL, &Val, NULL, &max_pt);
		if (Val > maxVal) {
			maxVal = Val;
			loc_x[0] = max_pt.x+before_x;
			loc_y[0] = max_pt.y+before_y;
		}
	}
	before_x = loc_x[0]-50;
	before_y = loc_y[0]-75;
	return (int)maxVal;
}


int mytemplatematch(unsigned char* capture_img,int *loc_x,int *loc_y) {	
	cv::Mat img(448, 384, CV_8UC3, capture_img);
	int width = img.size().width;
	int height = img.size().height;

	int min_error = 100000000;
	int min_error_locx = 0;
	int min_error_locy = 0;
	printf("a");
	for (int imgId = 0; imgId < 9; imgId++) {
		int temp_width = imgs[imgId].size().width;
		int temp_height = imgs[imgId].size().height;
		printf("height%d,temp_height%d\n",height,temp_height);

		for (int j = 0; j < height - temp_height; j++) {
			for (int i = 0; i < width - temp_width; i++) {
				int count = 0;
				for (int l = 0; l < temp_height; l++) {
					cv::Vec3b* src = img.ptr<cv::Vec3b>(j+l);
					cv::Vec4b* tmp_src = img.ptr<cv::Vec4b>(l);
					for (int k = 0; k < temp_width; k++) {

						for (int m = 0; m < 3; m++) {
							if (src[k + i][m] != tmp_src[k][m]) {
								count++;
								break;
							}
						}
					}
					if (count > min_error)break;
				}
				if (count < min_error) {
					min_error = count;
					min_error_locx = i;
					min_error_locy = j;
				}
			}
		}
	}
//	loc_x[0] = min_error_locx;
//	loc_y[0] = min_error_locy;
	return min_error;
}

//life=0
int check_array_coord1[3][2] = { {283,228},{273,189},{203,168} };//íÜìrîºí[
int check_array_value1[3][3] = { {87,87,174},{59,59,117},{126,126,126} };//íÜìrîºí[
int check_array_coord2[3][2] = { {251,203},{237,177},{249,187} };//íÜìrîºí[
int check_array_value2[3][3] = { {87,87,174},{90,90,179},{93,93,185} };//íÜìrîºí[


//life!=0
int check_array_coord3[2][2] = { {280,348},{225,357} };//íÜìrîºí[
int check_array_value3[2][3] = { {187,187,187},{33,41,45} };//íÜìrîºí[
int check_array_coord4[2][2] = { {436,44},{434,25} };//íÜìrîºí[
int check_array_value4[2][3] = { {0,0,0},{0,0,0} };//íÜìrîºí[

int KEYs[9][2] = { {VK_LEFT},{VK_UP},{VK_RIGHT},{VK_DOWN},{0},{VK_LEFT,VK_UP},{VK_LEFT,VK_DOWN} ,{VK_RIGHT,VK_UP},{VK_RIGHT,VK_DOWN} };


void step(int action, unsigned char* capture_img,int* reward,int* life,int* done) {

	life[0] = reward[0] = done[0] = 0;
	unsigned char life_board[48 * 144 * 3];
	capture_life_board(life_board);
	int height = 144 * 3;
	int width = 3;
	*reward += 1;

	for (int i = 0; i < 9; i++) {
		*life += life_board[8 * 144 * 3 + 16 * i + 2] / 128;
	}
	capture_foreground(capture_img);

	int shape[3] = {448, 384, 3};
	cv::Mat img(448, 384, CV_8UC3, capture_img);

	cv::flip(img, img, 0);
	if (*life == 0) {
		int count = 0;
		for (int i = 0; i < 3; i++)
		{
			for (int j = 0; j < 3; j++) {
				if (img.at<cv::Vec3b>(check_array_coord1[i][0], check_array_coord1[i][1])[j] == check_array_value1[i][j])count++;
			}
		}
		if (count == 9)
		{
			*done = 1;
			return;
		}
		count = 0;
		for (int i = 0; i < 3; i++)
		{
			for (int j = 0; j < 3; j++) {
				if (img.at<cv::Vec3b>(check_array_coord2[i][0], check_array_coord2[i][1])[j] == check_array_value2[i][j])count++;
			}
		}
		if (count == 9)
		{
			*done = 1;
			return;
		}
	}

	int count = 0;
	for (int i = 0; i < 2; i++)
	{
		for (int j = 0; j < 3; j++) {
			if (img.at<cv::Vec3b>(check_array_coord3[i][0], check_array_coord3[i][1])[j] == check_array_value3[i][j])count++;
		}
	}
	if (count == 6) {
		*done = 1;
		return;
	}

	count = 0;
	for (int i = 0; i < 2; i++)
	{
		for (int j = 0; j < 3; j++) {
			if (img.at<cv::Vec3b>(check_array_coord4[i][0], check_array_coord4[i][1])[j] == check_array_value4[i][j])count++;
		}
	}
	if (count == 6) {
		*done = 1;
		return;
	}


/*	int x, y;
	templatematch(capture_img,&x,&y);
	int min_x=x-100,max_x=x+100;
	int min_y=y-100,max_y=y+100;
	int paste_x=0, paste_y=0;
	if (x - 100 < 0) { min_x = 0; paste_x = 100 - x; }
	if (y - 100 < 0) { min_y = 0; paste_y = 100 - y; }
	if (x + 101 > 384) { max_x = 383; paste_x = 0; }
	if (y + 101 > 448) { max_y = 447; paste_y = 0; }
	cv::Rect roi(cv::Point(min_x, min_y), cv::Size(max_x - min_x, max_y - min_y));
	cv::Mat rect = img(roi);
	cv::Mat black(448,384,CV_8UC3,cv::Scalar(0));
	cv::Mat affine= (cv::Mat_<double>(2, 3) << 1.0, 0.0, paste_x, 0.0, 1.0, paste_y);
	cv::warpAffine(rect, black, affine, black.size(), cv::INTER_LINEAR, cv::BORDER_TRANSPARENT);
	cv::resize(black,black,cv::Size(), 384.0 / img.cols, 448.0 / img.cols);
	cv::imshow("xxx", black);

	
		for (int i = 0; i < 448 * 384 * 3; i++)
		capture_img[i] = black.data[i];



	//imgÇ©ÇÁéläpå`ÇêÿÇËèoÇ∑ÅAçïîwåiÇÃâÊëúÇ…ì\ÇÈ



	cv::resize(img, img, cv::Size(), 84.0 / img.cols, 84.0 / img.cols);*/

	keybd_event('Z', 0, 0, 0);
	for (int i = 0; i < 4; i++)
		if (KEYs[action][0] != KEYs[i][0] && KEYs[action][1] != KEYs[i][0]) {
			keybd_event(KEYs[i][0], 0, KEYEVENTF_KEYUP, 0);
		}

	for (int i = 0; i < 2; i++) {
		if (KEYs[action][i] != 0) {
			keybd_event(KEYs[action][i], 0, 0, 0);
		}
	}
	return;
}


