import json
import requests
import time
from bson.objectid import ObjectId
from cluster import MediaClusterBuilder, DistanceMode
from database_client import media_mongo_client
from StringIO import StringIO


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class MLServiceClient(object):
    @staticmethod
    def find_media_by_media_id(media_id, media_list):
        for media in media_list:
            source_url = media.get('source_url')
            if media_id in source_url:
                return media

    def get_ml_cluster(self, media_cluster):
        if len(media_cluster.media_list) > 1:
            # Construct post data.
            post_media_data = ''
            for media in media_cluster.media_list:
                post_media_data += '{}\n'.format(JSONEncoder().encode(media))

            # Sending request.
            print 'Sending request with {} media...'.format(len(media_cluster.media_list))
            url = 'http://52.7.233.119:3000/api/uploadPosts'
            files = {
                'filedata': StringIO(post_media_data),
                'classify': 'true'
            }

            response = requests.post(url, files=files)
            print response.text
            response_dict = json.loads(response.text)
            ml_clusters = response_dict.get('data', {}).get('clusters')
            if ml_clusters and len(ml_clusters) > 0:
                ml_clusters_data = list()
                for ml_cluster in ml_clusters:
                    media_ids = ml_cluster.get('postIds')
                    print '{} media cluster'.format(len(media_ids))
                    ml_cluster_data = list()
                    for media_id in media_ids:
                        ml_cluster_data.append(self.find_media_by_media_id(media_id, media_cluster.media_list))
                    ml_clusters_data.append(ml_cluster_data)
                return ml_clusters_data

    def cluster_and_send(self):
        # Call cluster to get initial clusters and send each cluster to ML server.
        media_cluster_builder = MediaClusterBuilder(DistanceMode.PAIRWISE_ALL)
        # Get all media of last 24 hours.
        now_timestamp_s = long(time.time())
        one_day_ago_timestamp_s = now_timestamp_s - 60 * 60 * 24
        media_results = media_mongo_client.search_media_by_time(one_day_ago_timestamp_s, now_timestamp_s)
        for media in media_results:
            media_cluster_builder.track_media(media)
        media_clusters = media_cluster_builder.get_clusters()
        media_clusters.sort(key=lambda cluster: cluster.media_count, reverse=True)
        print 'Generated {} clusters'.format(len(media_clusters))
        for media_cluster in media_clusters:
            self.get_ml_cluster(media_cluster)
