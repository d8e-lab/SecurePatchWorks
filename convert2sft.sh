export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5
torchrun --nproc-per-node 1 /mnt/42_store/sbc/bug_detection/convert2sft.py \
    --library_path "/mnt/42_store/sbc/bug_detection/build/java.so"\
    --language java\
    --dataset_dir "/mnt/42_store/sbc/bug_detection/datasets1025"\
    --model_path "/mnt/42_store/sbc/trans-opus-mt-en-zh"\
    --output_dir "/mnt/42_store/sbc/bug_detection/datasets_new"
