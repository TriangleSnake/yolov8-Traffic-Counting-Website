from ultralytics import YOLO
import object_counter
import cv2
import json




def run(token="test"):
    model = YOLO("yolov8x.pt")
    
    TOKEN = token    
    FILETYPE = "mp4"
    VIDEO_PATH = "./uploads/"+TOKEN+"/video"
    AREA_PATH = "./uploads/"+TOKEN+"/area.txt"
    OUTPUT_PATH = "./uploads/"+TOKEN+"/output." + FILETYPE
    RESULT_PATH = "./uploads/"+TOKEN+"/result.txt"
    CAP_PER_FRAME = 1
    FRAME_PATH = "./uploads/"+TOKEN+"/frame.jpg"


    with open(AREA_PATH, 'r') as f:
        area = json.loads(f.read())

    cap = cv2.VideoCapture(VIDEO_PATH)
    WIDTH = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    HEIGHT = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))



    counter = object_counter.ObjectCounter()
    counter.set_args(view_img=False,
                    reg_pts=area,
                    classes_names=model.names,
                    draw_tracks=True)


    video_writer = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter_fourcc(*'MP4V'), 20,(WIDTH, HEIGHT))

    while cap.isOpened():
        for _ in range(CAP_PER_FRAME):
            success, im0 = cap.read()
            
        if not success:
            print("Video frame is empty or video processing has been successfully completed.")
            break
        tracks = model.track(im0, persist=True, show=False)
        im0 = counter.start_counting(im0, tracks)
        cv2.imwrite(FRAME_PATH, im0)
        video_writer.write(im0)
    with open(RESULT_PATH, 'w') as f:
        f.write("OK")


    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()