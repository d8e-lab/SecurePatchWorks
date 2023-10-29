for file in /mnt/42_store/sbc/bug_detection/data_zips/*.zip; do
    dir="/mnt/42_store/sbc/bug_detection/datasets/$(basename $file .zip)"
    mkdir -p $dir
    # echo $dir
    unzip -qq "$file" -d "$dir"
done
count=$(ls -1 /mnt/42_store/sbc/bug_detection/datasets/ | wc -l)
echo "文件夹内的文件数量为: $count"