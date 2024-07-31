import decimal
import json
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import os
import sys

def verify_type(field_type, field_size):
    # print(field_type, field_size)
    new_type = None

    if type(field_type) == dict:
        new_type = pa.struct(list(build_schema(field_type)))
    elif type(field_type) == list:
        new_type = pa.list_(verify_type(field_type[0], None))
    elif field_type == 'string':
        new_type = pa.string()
    elif field_type == 'int':
        new_type = pa.int32()
    elif field_type == 'timestamp':
        new_type = pa.timestamp('us')
    elif field_type == 'date':
        new_type = pa.date32()
    elif field_type == 'double':
        new_type = pa.float64()
    elif field_type == 'float':
        new_type = pa.float32()
    elif field_type == 'boolean':
        new_type = pa.bool_()
    elif field_type.startswith('decimal'):
        precision, scale = field_size.split(',')
        new_type = pa.decimal128(int(precision), int(scale))

    return new_type

def build_schema(schema):
    # print(schema)
    for field_name, field in schema.items():
        field_description   = field['description']
        field_type          = field['type']
        field_size          = field['size']
        field_nullable      = True # field['nullable']

        # print(field_name, field_type, field_size, field_nullable, field_description)
        new_field = pa.field(
            name=field_name,
            type=verify_type(field_type, field_size),
            nullable=field_nullable,
            metadata={'description': field_description}
        )

        yield new_field

def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.strptime(value, "%Y-%m-%d")
        except:
            try:
                json_dict[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    json_dict[key] = datetime.fromisoformat(value)
                except:
                    pass
    return json_dict

layout = sys.argv[1]

with open(f'schema/{layout}.json', 'r') as f:
    dict_schema = json.load(f)

schema = pa.schema(
    metadata=None,
    fields=list(build_schema(dict_schema))
)

os.makedirs(f'input/{layout}', exist_ok=True)
os.makedirs(f'output/{layout}', exist_ok=True)

inputs = os.listdir(f'input/{layout}')

for input_file in inputs:
    with open(f'input/{layout}/{input_file}', 'r') as f:
        data = json.load(f, object_hook=date_hook, parse_float=decimal.Decimal)

    table = pa.Table.from_pylist(data, schema=schema)

    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')

    pq.write_table(table, f'output/{layout}/{layout}_{input_file.split(".")[0]}_{timestamp}.parquet')



