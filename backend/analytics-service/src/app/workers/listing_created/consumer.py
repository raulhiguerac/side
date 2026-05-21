import os
from confluent_kafka import Consumer

from app.services.prediction.use_cases.batch import BatchPrediction

from app.services.prediction.schemas.prediction import PredictionRequest

class Consumer:
    def __init__(self, uc: BatchPrediction) -> None:
        server = os.getenv('KAFKA_SERVER')
        group_id = os.getenv('KAFKA_GROUP_ID')
        topic = os.getenv('KAFKA_TOPIC')

        if not (server | group_id | topic):
            raise MISSMATCH KAFKA SERVER ERROR

        consumer = Consumer({
            'bootstrap.servers': server,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })

        consumer.subscribe([topic])

        self.uc = uc
        self.consumer = consumer
    
    def consume_batch(self):
        batch_messages = []

        while True:
            msg = self.consumer.poll(1.0)
            if msg:
                try:
                    value = msg.value().decode('utf-8')
                    batch_messages.append(value)
                except
            break
         
        schema = tuple(str,PredictionRequest) # schema registry es overhead si el contrato es estable 

        for _ in batch_messages:
            validate_schema()


