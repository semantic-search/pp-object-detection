FROM nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04
RUN apt-get update
RUN apt-get install -y python2.7 python-pip
RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
RUN apt-get -y install libopencv-dev python-opencv
RUN apt-get -y install wget
RUN apt-get -y install git
RUN pip install --upgrade pip
RUN pip install Cython
RUN pip install scikit-build
RUN wget https://paddle-wheel.bj.bcebos.com/0.0.0-gpu-cuda10-cudnn7-mkl/paddlepaddle_gpu-0.0.0-cp27-cp27mu-linux_x86_64.whl
RUN pip install opencv-python==4.2.0.32
RUN pip install paddlepaddle_gpu-0.0.0-cp27-cp27mu-linux_x86_64.whl
RUN python -c "import paddle; print(paddle.__version__)"
RUN pip install visualdl
RUN pip install PyYAML 
RUN pip install shapely python-dotenv kafka-python
RUN git clone https://github.com/cocodataset/cocoapi.git
RUN cd cocoapi/PythonAPI && make install
RUN git clone https://github.com/PaddlePaddle/PaddleDetection.git
WORKDIR PaddleDetection
RUN wget https://paddlemodels.bj.bcebos.com/object_detection/retinanet_x101_vd_64x4d_fpn_1x.tar
RUN pip install tqdm
RUN python ppdet/modeling/tests/test_architectures.py 
COPY . .
RUN mkdir uploads
RUN mkdir workspace
RUN apt-get -y install python-tk
EXPOSE 5000
CMD ["python", "app.py"]
