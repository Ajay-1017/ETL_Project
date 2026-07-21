import logging 
import extract
import transform
import config


def my_logger():

    logging.basicConfig(
        filename = config.LOG_PATH,
        format = "'%(asctime)s | %(levelname)s | %(message)s ",
        level = logging.DEBUG
    )

    # Data Extraction
    data = extract.extract_data()
   
    # Data Transformation
    etl = transform.Transform(data)
    etl.run()   

    reject_df = etl.reject_logs

    for _ , df in reject_df.items():
        if not df.empty:
            for _ , row in df.iterrows():
                logging.info(row.to_dict())

my_logger()








