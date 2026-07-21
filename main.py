import extract
import transform
import load


def main():
    # Data Extraction
    data = extract.extract_data()
   
    # Data Transformation
    t = transform.Transform(data)
    final_tables = t.run()

    # Data Loading
    load.load_data(final_tables)

if __name__=="__main__":
    main()
    














