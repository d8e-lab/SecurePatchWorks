page=101
while [ $page -le 200 ] ; do
    url="https://samate.nist.gov/SARD/api/test-cases/search?language%5B%5D=java&page=${page}&limit=100"
    echo $url
    curl -o apis1029/api_$page.json $url
    page=$((page+1))
done
python /mnt/42_store/sbc/bug_detection/download_datasets.py \
    --output_dir "/mnt/42_store/sbc/bug_detection/data_zips"\
    --api_dir "/mnt/42_store/sbc/bug_detection/apis1029"