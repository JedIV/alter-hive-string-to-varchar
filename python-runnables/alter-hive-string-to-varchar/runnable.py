# This file is the actual code for the Python runnable alter-hive-string-to-varchar
from dataiku.runnables import Runnable
from dataiku.core.sql import HiveExecutor
import pprint
import dataiku
import json

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    input_dataset_name = None
    input_cols_map = None
    query_ds = None #dataiku.Dataset() object
    hive_executor = None
    
    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
        input_dataset_name = config.get('input_dataset')
        input_cols_map = config.get('input_cols_map')
        if not input_cols_map:
            raise ValueError('List of columns to modify is empty')
        
        self.dssh = dataiku.api_client()
        self.project = self.dssh.get_project(project_key)
        
        dataset_list = [d['name'] for d in self.project.list_datasets()]
        print('dataset list: %s' % dataset_list)
        if input_dataset_name not in dataset_list:
            raise ValueError('Input dataset {} not found in project datasets {}'.format(input_dataset_name, dataset_list))
        
        self.input_dataset = self.project.get_dataset(input_dataset_name)
        self.input_dataset_schema = self.input_dataset.get_schema()
        print('Retreived DSS schema for input dataset {}'.format(input_dataset_name))
        pprint.pprint(self.input_dataset_schema)

        eligible_columns = [c['name'] for c in self.input_dataset_schema['columns'] if c['type'] == 'string']
        print('Eligible columns (with string type only): %s' % eligible_columns)
        for col_key in input_cols_map.keys():
            if col_key not in eligible_columns:
                raise ValueError('Column to modify {} is either not present or not of string type'.format(col_key))

        #Basic sanity checks done - fixing the instance objects
        self.input_cols_map = input_cols_map        
        self.query_ds = dataiku.Dataset(input_dataset_name, project_key=self.project_key)
        self.hive_executor = HiveExecutor(dataset=self.query_ds)        
        self.input_dataset_name = input_dataset_name
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def get_hive_schema(self, pre_queries=None):
        describe_query = 'DESCRIBE {}'.format(self.input_dataset_name)
        print('Executing query {}'.format(describe_query))
        res_iter = self.hive_executor.query_to_iter(describe_query, pre_queries=pre_queries)
        
        return [l for l in res_iter.iter_tuples()]
        
    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        prev_sch = self.get_hive_schema()

        alter_query_fmt = "ALTER TABLE {table} CHANGE COLUMN {colname} {colname} VARCHAR({colsize})"
        
        pre_queries = []
        for col_key in self.input_cols_map.keys():
            alter_query = alter_query_fmt.format(table=self.input_dataset_name, colname=col_key, colsize=self.input_cols_map[col_key])
            print('Appending to pre-queries query: {}'.format(alter_query))
            pre_queries.append(alter_query)

        #push ALTER statement to pre-queries of the DESCRIBE to avoid connecting multiple times
        new_sch = self.get_hive_schema(pre_queries=pre_queries)

        result ={'previous_schema': prev_sch,
                  'new_schema': new_sch}
        
        return '<pre>' + json.dumps(result) + '</pre>'
        