#  Quick Start

## 環境構築
**必須ツール**
- chrome

### Anaconda

```
conda create -n scraping --file conda_requirements.txt
conda activate scraping
```

### pip

```
pip install -r requirements.txt
```

## スクレイピングする
### SUUMOをスクレイピングする

```python
python main.py --target-suumo
```

### じゃらんをスクレイピングする

```python
python main.py --target=jalan
```

**引数について**

|引数|概要|
|:--:|:--:|
|pref_name=Yamagata|指定された県のスクレイピングを行う|
|target=suumo|suumoかjalanを指定することで指定した方のスクレイピングをします|
|page_interval=60|indexページが変化するごとに設けるインターバル（秒）|
|img_interval=30|画像が変化するごとに設けるインターバル（秒）|
img10_interval=30|suumoのみで10枚以上一つの物件に画像があるときに設けるインターバル（秒）|

## 結果の保存先
　スクレイピング結果は、SUUMOの場合は、画像は```/imgs/suummo/```に```{house_od}_{img_id}```の形式で保存されています。各物件の属性情報は、```csv/suumo/```に```attribute_{prefecture_name}_{page_num}.csv```として、画像と物件情報の対応シートは```csv/suumo/```に```imgs_{prefecture_name}_{page_num}.csv```として保存されています。

　jalanの場合は、画像は```/imgs/jalan/```に```{landmark_id}_{review_id}_{img_id}```の形式で保存されています。各物件の属性情報は、```csv/jalan/```に```attribute_{prefecture_name}_{landmark_count}.csv```として、画像と物件情報の対応シートは```csv/suumo/```に```imgs_{prefecture_name}_{landmark_count}.csv```として保存されています。