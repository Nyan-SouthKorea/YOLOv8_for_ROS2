# 파이썬 기본 패키지
import threading
import time
from copy import deepcopy

# 추가 설치 패키지
from ultralytics import YOLO
import numpy as np
import cv2
import torch

class Custom_YOLOv8:
    def __init__(self, model_name='yolov8n.pt', filter=None):
        '''
        입력되는 Image와 Depth Map에서 사물인식하여, 감지된 사물의 결과의 x, y, depth 정보를 반환
        
        model_name : YOLOv8 model 이름 입력(yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt, 혹은 custom model 입력)
        filter : 감지를 원하는 특정 사물이 있을 경우 list형태로 입력. None일 경우 모두 추론(None or ['person', 'cat'])
        '''
        print('자세한 기능 사용법 안내: https://github.com/Nyan-SouthKorea/YOLOv8_for_ROS2')
        self._check_cuda()
        self.model = YOLO(model_name)
        self.filter = filter
        self.img = None
        self.depth_map = None
        self.dic_list = []
        self.run_request = False
        self.stop_request = False
        self.thread = threading.Thread(target = self._prediction_thread)
        self.thread.start()


    def run(self, img, depth_map, conf_thresh=0.65):
        '''
        추론하기 원하는 image와 depth_map을 입력.
        class 내부에서 multi-thread로 구동되는 YOLOv8 모델에 img와 depth_map을 업데이트하고 지금까지 처리된 가장 최근의 추론 결과를 반환.
        (이렇게 처리하는 이유는, 성능이 낮은 컴퓨터에서도 렉이 걸리지 않게끔 보이기 위해서임)
        
        img : cv2로 처리할 수 있는 numpy 배열의 bgr 이미지
        depth_map : numpy 배열의 2차원 1채널 거리 정보(안에 숫자들은 int, float 상관 없음)
        conf_thresh : confidence threshold 설정
        '''
        # 처리해야 하는 img, depth_map 업데이트
        self.img = img
        self.depth_map = depth_map
        self.conf_thresh = conf_thresh
        self.run_request = True
        
        # 가장 최근까지 처리된 추론 결과 반환
        if self.dic_list == []:
            return_value = False
        else:
            return_value = True
        return return_value, self.dic_list
    
    def draw(self):
        '''
        내부 변수 self.img와 self.dic_list를 활용하여 그려서 결과 반환
        '''
        img = deepcopy(self.img)
        dic_list = deepcopy(self.dic_list)
        for dic in self.dic_list:
            cv2.rectangle(img, (dic['bbox'][0], dic['bbox'][1]), (dic['bbox'][2], dic['bbox'][3]), (0,0,255), 2)
            text = f'{dic["class_name"]}:{round(dic["conf"], 2)}, depth: {dic["depth"]}'
            cv2.putText(img, text, (dic['bbox'][0], dic['bbox'][1]+25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        return img
    
    def stop(self):
        '''
        멀티쓰레드를 종료한다
        '''
        self.stop_request = True


    def _prediction_thread(self):
        '''
        run 함수에서 업데이트된 self.img와 self.depth_map을 multi-thread로 처리하여 추론 결과를 self.dic_list에 업데이트 함
        '''
        class_list = None
        while True:
            # 종료 조건
            if self.stop_request == True:
                break

            # run()에서 이미지를 투입할 때 마다 구동
            if self.run_request == False:
                time.sleep(0.01)
                continue
            self.run_request = False

            # run()에서 투입된 정보가 로직이 실행되는 중간에 섞이지 않도록 내부 함수로 업데이트
            img = deepcopy(self.img)
            depth_map = deepcopy(self.depth_map)
            conf_thresh = deepcopy(self.conf_thresh)

            # 추론
            results = self.model.predict(source = cv2.cvtColor(img, cv2.COLOR_BGR2RGB), verbose = False)[0]
            if class_list == None:
                class_list = results.names
            results = results.boxes.data.tolist()
            dic_list = []
            for result in results:
                x1, y1, x2, y2, conf, cls = int(result[0]), int(result[1]), int(result[2]), int(result[3]), round(float(result[4]), 2), int(result[5])
                class_name = class_list[cls] # class이름 추출
                # conf_thresh 넘는 경우만 계산
                if conf < conf_thresh:
                    continue

                # 만약 filter를 설정해 놓았을 경우, 원하는 class만 감지하기
                if self.filter != None:
                    if not class_name in self.filter:
                        continue

                # 감지된 사물의 x, y 포인트 계산
                center_x = int((x2+x1)/2)
                center_y = int((y2+y1)/2)
                # depth 계산
                depth = self._get_depth(depth_map, [x1,y1,x2,y2]) # depth 추출
                dic_list.append({'bbox':[x1, y1, x2, y2], 'conf':conf, 
                                 'class_name':class_name, 'center_x':center_x, 'center_y':center_y, 'depth':depth})
            # 실시간 추론값 업데이트
            self.dic_list = deepcopy(dic_list)

    def _get_depth(self, depth_map, bbox, rate=0.3):
        '''
        depth_map에서 bbox영역의 중앙 영역 depth를 반환

        depth_map : 내부 변수
        bbox : 내부 변수
        rate : bbox 면적에서 해당 rate만큼의 중앙 영역의 평균 값을 계산함
        '''
        # rate 반영한 bbox 계산
        x1, y1, x2, y2 = bbox
        # bbox의 가로 세로 길이
        x_len = x2-x1
        y_len = y2-y1
        # rate 반영한 bbox의 가로 세로 길이
        new_x_len = x_len*rate
        new_y_len = y_len*rate
        # rate 반영된 bbox 수치 계산
        new_x1 = x1 + ((x_len-new_x_len)/2)
        new_y1 = y1 + ((y_len-new_y_len)/2)
        new_x2 = x2 - ((x_len-new_x_len)/2)
        new_y2 = y2 - ((y_len-new_y_len)/2)
        new_x1, new_y1, new_x2, new_y2 = int(new_x1), int(new_y1), int(new_x2), int(new_y2)
        # depth_map에서 원하는 부분 crop하여 평균 depth 구하기
        crop_depth = depth_map[new_y1:new_y2, new_x1:new_x2]
        mean_depth = np.mean(crop_depth)
        return round(mean_depth, 2)
    
    def _check_cuda(self):
        '''
        현재 설치된 torch 환경이 YOLO를 GPU에서 구동할 수 있는 환경인지 검사
        '''
        if torch.cuda.is_available():
            print('GPU 사용 가능')
        else:
            print('GPU 사용 불가. CPU를 통한 추론만 가능')
        

if __name__ == '__main__':
    custom_YOLOv8 = Custom_YOLOv8(model_name='yolov8n.pt', filter=['person'])
    cap = cv2.VideoCapture(0)
    while True:
        # 웹캠 수신
        ret, img = cap.read()
        if ret == False:
            print('웹캠 수신 안됨')
            break
        
        # 더미 depth파일 생성
        h, w, c = img.shape
        depth_map = np.random.randint(0, 256, (w, h), dtype=np.uint8)

        # 인퍼런스
        ret, dic_list = custom_YOLOv8.run(img, depth_map)
        if ret:
            print(dic_list)
        else:
            print('감지 내역 없음')
        draw_img = custom_YOLOv8.draw()
        
        cv2.imshow('test', draw_img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            custom_YOLOv8.stop()
            break