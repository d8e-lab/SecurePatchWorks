for file in data_zips/*.zip; do
    dir="datasets/$(basename $file .zip)"
    mkdir -p $dir
    # echo $dir
    unzip -qq "$file" -d "$dir"
done
count=$(ls -1 datasets/ | wc -l)
echo "文件夹内的文件数量为: $count"
bash /home/xmu/sbc/SecurePatchWorks/convert2sft.sh