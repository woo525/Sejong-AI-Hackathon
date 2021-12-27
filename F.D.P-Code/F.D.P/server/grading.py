#https://www.youtube.com/watch?v=W9oRTI6mLnU
# window-949 csv 안열리면 https://codingcoding.tistory.com/609

"""
---------------------------------------------------------------------
주의 사항
1. 시험지는 평평한 곳에서 찍어야 인식이 잘된다.
2. 체크박스는 최대한 까맣게 칠하기 (컴싸 잘됨)
3. 화질 너무 안좋으면 detect 안됨

--------------------------------------------------------------------
"""
import  cv2
from PIL import Image
import pytesseract
import time
import numpy as np
import uuid
import os
import pandas as pd
from openpyxl import Workbook
import xlsxwriter
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# setting ->pytessa ->0.3.4 하면 빈박스 안나옴

def main():
    StudentAnswers = 'StudentAnswers'  # 각 문항별로 학생들의 답이 저장될 폴더


    TFanswer=['True','True','False','False','False']# t t f f f true/false 문항 정답
    per = 25
    pixelThreshold = 1000 # 체크박스 t / f 구분 기준

    roi = [[(1822, 792), (1858, 830), 'agreebox', 'agree'],
        #[(884, 858), (1296, 934), 'text', 'id'],
        #[(1568, 864), (2028, 936), 'text', 'name'],
        [(422, 1122), (458, 1160), 'box', 'true1'],
        [(416, 1242), (458, 1280), 'box', 'true2'],
        [(421, 1363), (454, 1396), 'box', 'true3'],
        [(424, 1486), (456, 1520), 'box', 'true4'],
        [(422, 1606), (451, 1639), 'box', 'true5'],
        [(1238, 1078), (2178, 1202), 'text', 'short6'],
        [(1238, 1206), (2182, 1340), 'text', 'short7'],
        [(1236, 1338), (2180, 1472), 'text', 'short8'],
        [(1234, 1472), (2177, 1607), 'text', 'short9'],
        [(1239, 1609), (2177, 1729), 'text', 'short10'],
        [(254, 1829), (2220, 3279), 'text', 'essay11']]
    # 위치 찾기

    imgQ = cv2.imread('test.jpeg') #답안 jpg #빈시험지
    h,w,c = imgQ.shape
    #mgQ= cv2.resize(imgQ,(w//3,h//3))

    orb = cv2.ORB_create(10000)   #########잘 안되면 바꿔보기
    kp1, des1 = orb.detectAndCompute(imgQ,None)
    impKp1 = cv2.drawKeypoints(imgQ,kp1,None)

    #cv2.imshow("keyPintQuery",impKp1)

    allData=[["id","agree","true1","true2","true3","true4","true5","short6","short7","short8","short9","short10","essay11"]] # 카테고리
    path = 'UserForms2' # 학생들 답안(캡쳐쳐 모음
    myPicList = os.listdir(path)
    print(myPicList)
    for j,y in enumerate(myPicList):
        img = cv2.imread(path + "/" +y)
        #img = cv2.resize(img, (w // 3, h // 3))
        #  cv2.imshow(y, img)
        kp2, des2 = orb.detectAndCompute(img,None)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        matches = bf.match(des2,des1)
        matches.sort(key = lambda x:x.distance)
        good = matches[:int(len(matches)*(per/100))]
        imgMatch = cv2.drawMatches(img,kp2,imgQ,kp1,good[:100],None,flags=2)

        #cv2.imshow(y, imgMatch)

        srcPoints = np.float32([kp2[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dstPoints = np.float32([kp1[m.trainIdx].pt for m in good ]).reshape(-1,1,2)

        M, _ = cv2.findHomography(srcPoints,dstPoints,cv2.RANSAC,5.0)
        imgScan = cv2.warpPerspective(img,M,(w,h))

        #cv2.imshow(y, imgScan)
        imgShow = imgScan.copy()
        imgMask = np.zeros_like(imgShow)


        myData = [y[:-4]]
        print(f'##########Extracting Data from Form {j}############')

        for x, r in enumerate(roi):
            cv2.rectangle(imgMask, (r[0][0], r[0][1]), (r[1][0], r[1][1]), (0, 255, 0), cv2.FILLED)
            imgShow = cv2.addWeighted(imgShow, 0.99, imgMask, 0.1, 0)  ##바꿀수 있음

            imgCrop = imgScan[r[0][1]:r[1][1], r[0][0]:r[1][0]]
            # cv2.imshow(str(x), imgCrop) # 답 조각조각

            if r[2] == 'text':  # 답 텍스트로 가져오는거
                #print(f'{r[3]}:{pytesseract.image_to_string((imgCrop))}')  ##답안 하나하나 출력
                #myData.append(pytesseract.image_to_string((imgCrop)))
                imgPath =os.path.join(StudentAnswers,r[3],y)
                cv2.imwrite(os.path.join(imgPath),imgCrop)
                myData.append(imgPath)
                #print(x)
            if r[2] == 'box':  # 체크박스
                imgGray = cv2.cvtColor(imgCrop, cv2.COLOR_BGR2GRAY)
                imgThresh = cv2.threshold(imgGray, 170, 255, cv2.THRESH_BINARY_INV)[1]
                totalPixels = cv2.countNonZero(imgThresh)
                print("dfdfdfdf")
                print(totalPixels )
                if totalPixels > pixelThreshold:
                    totalPixels = 1;
                    myAns = 'True'
                else:
                    totalPixels = 0
                    myAns = 'False'
                #print(f'{r[3]}:{totalPixels}')
                myData.append(myAns)  # 1:체크o 0:체크x
            if r[2] == 'agreebox':  # 동의 체크박스
                imgGray = cv2.cvtColor(imgCrop, cv2.COLOR_BGR2GRAY)
                imgThresh = cv2.threshold(imgGray, 170, 255, cv2.THRESH_BINARY_INV)[1]
                totalPixels = cv2.countNonZero(imgThresh)
                # print(totalPixels )
                if totalPixels > pixelThreshold:
                    totalPixels = 1;
                    myAns='agree'
                else:
                    totalPixels = 0
                    myAns='disagree'
                #print(f'{r[3]}:{totalPixels}')
                myData.append(myAns)  # 1:체크o 0:체크x

            cv2.putText(imgShow,str(myData[x+1]),(r[0][0],r[0][1]),
                        cv2.FONT_HERSHEY_PLAIN,2.5,(0,0,255),4)

        allData.append(myData)
        imgShow = cv2.resize(imgShow, (w // 3, h // 3))
        print(myData)
        #cv2.imshow(y+"2", imgShow)
    ##########################################csv화
    df = pd.DataFrame(allData)
    df.columns=["id","agree","true1","true2","true3","true4","true5","short6","short7","short8","short9","short10","essay11"]
    df.to_csv("csvResult.csv",index=False)


    ###########################################엑셀화
    #print(allData[2][7])
    # #https://www.youtube.com/watch?v=3mWqQlYlFlY  엑셀 이미지 삽입
    workbook = xlsxwriter.Workbook('excelResult.xlsx')
    worksheet = workbook.add_worksheet()
    row = 0
    col = 0
    image_width = 500
    image_height = 200

    cell_width =130
    cell_height = 50

    x_scale = cell_width/image_width
    y_scale = cell_height/image_height

    worksheet.set_column('H:N',35)
    worksheet.set_default_row(25)
    head_format = workbook.add_format({'bold':True,'valign':'center','font_size':15})
    wrongAns_format = workbook.add_format({'valign':'center','font_color':'red'})
    correctAns_format = workbook.add_format({'valign':'center','font_color':'green'})
    norm_format = workbook.add_format({'valign':'center'})
    disagree_format = workbook.add_format({'valign':'center','bg_color':'yellow'})

    worksheet.set_row(0,None,head_format)

    for line in allData:
        for item in line:
            if(item[-3:]=="jpg") :
                if('essay' in item):
                    worksheet.write_url(row,col,item,norm_format)
                else:
                    worksheet.insert_image(row,col,item,{'x_scale': x_scale, 'y_scale': y_scale})
            else:
                if row==0: #카테고리
                    worksheet.write(row, col, item,head_format)
                elif item!='True' and item!= 'False': #id , agree
                    if item =='disagree':
                        worksheet.write(row,col,item,disagree_format)
                    else:
                        worksheet.write(row, col, item, norm_format)
                else:# true false 문제
                    if(TFanswer[col-2]==item): # -2는 id, agree 항목때문에
                        worksheet.write(row,col,item,correctAns_format)
                    else:
                        worksheet.write(row,col,item,wrongAns_format)
            col+=1
        row += 1
        col = 0
    workbook.close()
    #os.system("excelResult.xlsx")
    #cv2.imshow("Output",imgQ)
    #cv2.waitKey(0)
    #https://www.youtube.com/watch?v=cUOcY9ZpKxw 17:13