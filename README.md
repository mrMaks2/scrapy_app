# Scrapy-приложение

Это простое приложение по скрапингу интернет-магазина.

## Инструкция по запуску приложения

1.  Клонируйте репозиторий:

    ```bash
    git clone https://github.com/mrMaks2/test_task_Brandquad.git
    ```

2.  Установите виртуальное окружение:

    ```bash
    virtualenv venv
    ```

3.  Активируйте виртуальное окружение:

    ```bash
    venv\Scripts\activate
    ```

4.  Установите зависимости:

    ```bash
    pip install -r requirements.txt
    ```

5.  Перейдите в директорию с кодом:
    
    ```bash
    cd alkoteka
    ```
 
6.  Запустите приложение:

    ```bash
    scrapy crawl spider_name -O result.json
    ```