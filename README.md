# YOLOv8_for_ROS2
ROS2 강의에서 YOLOv8 사물인식 파트에 대한 강의 자료


# Ubuntu 20.04 초기 설정 및 YOLOv8 환경 구축

## 처음 우분투 세팅

```bash
sudo apt update
sudo apt upgrade
sudo apt install python3-pip
sudo apt install python3.8-venv
```

## 가상환경 만들고 실행하기

```bash
python3.8 -m venv yolo
source yolo/bin/activate
```

## YOLOv8 패키지 설치하기

```bash
pip3 install ultralytics
```

## 내 PC에서 GPU를 사용하여 YOLO를 돌릴 수 있는지 확인하기

1. 가상환경 활성화

    ```bash
    source yolo/bin/activate
    ```

2. 파이썬 인터프리터 실행

    ```bash
    python3
    ```

3. GPU 사용 가능 여부 확인

    ```python
    import torch
    torch.cuda.is_available()
    ```

    - 만약 `True`가 출력되면 GPU가 잡힌 것입니다.
    - `False`가 출력되면 CPU를 사용하게 됩니다.

    무거운 모델을 구동할 것이 아니라면 크게 상관 없습니다.