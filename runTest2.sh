LD_LIBRARY_PATH=/usr/local/cuda-10.1/lib PYTHONPATH=$PYTHONPATH:. python anonymizer/bin/anonymize.py --input gothru-images --image-output gothru-output-images --weights weights --face-threshold 0.001 --plate-threshold 0.001 
