from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO('yolov8n.pt') 
    model.train(data='Dataset/data.yaml', epochs=30, imgsz=640, project='runs', name='forklift_human_model', resume=False)
