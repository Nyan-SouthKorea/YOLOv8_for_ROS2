from setuptools import setup, find_packages

# README 파일을 UTF-8 인코딩으로 읽어옵니다.
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='ros2_object_detection',
    version='1.0.4',
    description='return prediction information for ros2 autonomous driving from image and depth map',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Na-I-Eon',
    author_email='112fkdldjs@naver.com',
    url='https://github.com/Nyan-SouthKorea/YOLOv8_for_ROS2',
    packages=find_packages(),
    install_requires=[
        'ultralytics'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
