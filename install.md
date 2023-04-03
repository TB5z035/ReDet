conda create -n redet python=3.7 -y
conda activate redet

conda install cython
pip install torch==1.8.1+cu111 torchvision==0.9.1+cu111 torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html

export CUDA_HOME=/usr/local/cuda-11
find . -type f -exec sed -i 's/TORCH_CHECK/TORCH_CHECK/g' {} +

pip install -e .