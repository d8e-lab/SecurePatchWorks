export CUDA_VISIBLE_DEVICES=6
torchrun --nproc-per-node 1 convert2sft.py \
    --library_path "/home/xmu/sbc/SecurePatchWorks/tree-sitter/build/java_c_python.so"\
    --language c\
    --dataset_dir "datasets"\
    --model_path "/mnt/40_store/LLM/trans-opus-mt-en-zh/"\
    --output_dir "datasets_sft"
