Requirements

    Python 3
    PyTorch tested on 1.4.0, 1.5.0
    json
    PIL
    skimage
    tqdm
    cv2



//download pretrained model

sh ./scripts/download_trained_model.sh


//run example in mTest

python -m apps.simple_test -i ./mTest --use_rect