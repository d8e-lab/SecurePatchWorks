export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
torchrun --nproc-per-node 8 convert_sft.py \
    --library_path "/mnt/42_store/sbc/bug_detection/build/java.so"\
    --language java\
    --dataset_dir "/mnt/42_store/sbc/bug_detection/datasets"\
    --model_path "/mnt/42_store/sbc/trans-opus-mt-en-zh"\
    --output_dir "/mnt/42_store/sbc/bug_detection/datasets_new"
