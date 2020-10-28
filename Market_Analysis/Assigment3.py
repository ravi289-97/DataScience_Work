# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 11:00:09 2020

@author: Ravi Teja
"""
import pyspark
from pyspark.sql import SparkSession
from pyspark import SparkContext
from pyspark import SparkConf
import findspark as fs
import os
import pandas as pd
import matplotlib.pyplot as plt


os.environ["JAVA_HOME"] = "D:\Softwares\Java\jdk-14.0.1"
os.environ["SPARK_HOME"] = "D:\SPark\spark-3.0.1-bin-hadoop2.7"
fs.find()
fs.init()

conf=pyspark.SparkConf().setAppName("BankingProject").setMaster('local')
sc=pyspark.SparkContext(conf=conf)
spark=SparkSession(sc)

#Reading the data
df=spark.read.option("multiline","true").json("D:/Simplilearn/Big data/bank_edited.json")
df.show()

#Registering as temp table for sql query
df.registerTempTable("datanewtable")

#Running sql queries

#Sample Query
x=spark.sql("SELECT MAX(age) as maxAge FROM datanewtable").first().asDict()['maxAge']

#Count of people who subscribed
spark.sql("select count(*) as subscribed from datanewtable where y='yes'").show()
val1=spark.sql("select count(*) as subscribed from datanewtable where y='yes'").first().asDict()['subscribed']

#Market success rate
success_rate=val1/spark.sql("select count(*) as total from datanewtable").first().asDict()['total']
print("The success rate: {:.2f}%".format(success_rate*100))

#Market failure rate
spark.sql("select count(*) as unsubscribed from datanewtable where y='no'").show()
val2=spark.sql("select count(*) as unsubscribed from datanewtable where y='no'").first().asDict()['unsubscribed']
failure_rate=val2/spark.sql("select count(*) as total from datanewtable").first().asDict()['total']
print("The failure rate: {:.2f}%".format(failure_rate*100))

#Min,Max and mean of the age
max_val=df.select("age").rdd.max()[0]
min_val=df.select("age").rdd.min()[0]

from pyspark.sql.functions import mean as _mean, col

df_stats = df.select(
    _mean(col('age')).alias('mean'),
).collect()

mean = df_stats[0]['mean']

print("The max value of age: {}\n The min value of age: {}\n The mean value of age: {}".format(min_val,max_val,mean))



#quality of customers by checking average balance, median balance of customers

mean_balance=df.select(
    _mean(col('balance')).alias('mean_balance'),
).collect()[0]['mean_balance']

print("The mean balance is : {}".format(mean_balance))

median_balance=spark.sql("SELECT percentile_approx(balance, 0.5)as median FROM datanewtable").first(). asDict()['median']

print("The median balance is : {}".format(median_balance))

#Checking if age matters the marketing subscription cost
y=spark.sql("select age, count(*) as number from datanewtable where y='yes' group by age order by number desc")
y.show()

#Checking if marital status matters the subscription
maritaldata = spark.sql("select marital, count(*) as number from datanewtable where y='yes' group by marital order by number desc")
maritaldata.show()

#Checking if both age and marital status matters the subscription
ageandmaritaldata = spark.sql("select age, marital, count(*) as number from datanewtable where y='yes' group by age,marital order by number desc")
ageandmaritaldata.show()

#Feature Engineering on age
def update_age(age):
    if age<20:
        return "teen"
    elif age>=20 and age<=32:
        return "Young"
    elif age>32 and age<=55:
        return "middle age"
    else:
        return "old"

from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, StringType
from pyspark.sql.functions import udf
from pyspark.sql import Row

age_str=udf(lambda x:update_age(x),StringType())
spark.udf.register("age_str",age_str )

df2=spark.sql("select age,balance,y,age_str(age) as Ageclass from datanewtable")
df2.show()

df2.registerTempTable("banktable")

#Which age group subscribed more
targetage = spark.sql("select Ageclass, count(*) as number from banktable where y='yes' group by Ageclass order by number desc")
targetage.show()

#Pipelining with StringIndexer

from pyspark.ml.feature import IndexToString, StringIndexer

indexer = StringIndexer(inputCol="Ageclass", outputCol="ageindex")
model = indexer.fit(df2)
model.transform(df2).select("Ageclass","ageindex").show(10)
