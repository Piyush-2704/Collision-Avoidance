import cv2 as cv
from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
from math import *
import pyttsx3

model = YOLO('runs/forklift_human_model2/weights/best.pt')
#model = YOLO('yolov8n.pt')
model.to("cuda")
ptracker = DeepSort(max_age=25,n_init=3,embedder_gpu=True)
ftracker =DeepSort(max_age=25,n_init=3,embedder_gpu=True)   

def alert():
    engine = pyttsx3.init()
    engine.say("Manpower nearby be alert!!!")
    engine.runAndWait()

pc={}
flag=1
min_dis = 500
def avoid_collision(frame):
    global pc,flag,min_dis

    pdetections,fdetections=[],[]
    results=model.predict(source=frame,conf=0.75)[0]
    for result in results.boxes:
        cls_id=int(result.cls[0])
        x1,y1,x2,y2 = map(int,result.xyxy[0])
        conf = float(result.conf[0])
        if model.names[cls_id] == "person":
            pdetections.append(([x1,y1,x2-x1,y2-y1],conf,cls_id))
        elif model.names[cls_id] == "forklift":
            fdetections.append(([x1,y1,x2-x1,y2-y1],conf,cls_id))
    ptracks = ptracker.update_tracks(pdetections,frame=frame)
    ftracks = ftracker.update_tracks(fdetections,frame=frame)
    nc = {}
    for i in range(len(ptracks)):
        if ptracks[i].is_confirmed():
            print('a')
            for j in range(len(ftracks)):
                if ftracks[j].is_confirmed():
                    iid = ptracks[i].track_id
                    ix1,iy1,ix2,iy2 = map(int,ptracks[i].to_ltrb())
                    ic = ((ix1+ix2)/2,(iy1+iy2)/2)
                    nc[iid]=ic
                    jid = ftracks[j].track_id
                    jx1,jy1,jx2,jy2 = map(int,ftracks[j].to_ltrb())
                    jc=((jx1+jx2)/2,(jy1+jy2)/2)
                    nc[jid]=jc

                    dx,dy = ic[0]-jc[0],ic[1]-jc[1]
                    dis = sqrt(dx**2+dy**2)

                    if dis < min_dis:
                        if iid in pc and jid in pc:
                            iv = (ic[0]-pc[iid][0],ic[1]-pc[iid][1])
                            jv = (jc[0]-pc[jid][0],jc[1]-pc[jid][1])
                            v = (jv[0] - iv[0],jv[1]-iv[1])
                            dotp = dx*v[0] +dy*v[1]
                            if dotp<0:
                                if flag==1:
                                    alert()
                                    flag=0
                            else:
                                flag=1


    for track in ptracks + ftracks:
        if track.is_confirmed():
            #print('a')
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            print(x1,y1,"done")

    pc=nc.copy()
    return frame