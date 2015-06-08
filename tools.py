import sys
import time
import traceback
from cluster import DistanceMode, MediaClusterBuilder
from database_client import mongo_client
from flask import Flask
from flask import render_template
from ml_service_client import MLServiceClient


_CLUSTER_INFO_TEMPLATE = '<div class="clusterInfo"><a href="{0}" target="_blank">{1} media</a><br /><p>{2}</p>{3}</div>'
_ML_CLUSTER_INFO_TEMPLATE = '<div class="mlClusterInfo">{0} ML clusters<br />{1}</div>'
_ML_CLUSTER_CONTENT_TEMPLATE = 'Cluster: <p>{0}</p>'
_MEDIA_IMAGE_TEMPLATE = '<img src="{0}" />'

app = Flask(__name__)

@app.route('/')
def internal_tools():
    try:
        return render_template('tools.html')
    except:
        traceback.print_exc(file=sys.stdout)


@app.route('/verify_clusters')
def verify_clusters_tool():
    try:
        media_cluster_builder = MediaClusterBuilder(distance_mode=DistanceMode.PAIRWISE_ALL)
        now_timestamp_s = long(time.time())
        one_day_ago_timestamp_s = now_timestamp_s - 60 * 60 * 24
        media_results = mongo_client.search_media_by_time(one_day_ago_timestamp_s, now_timestamp_s)
        data = dict()
        data['db_time_spent'] = int(time.time() - now_timestamp_s)
        for media in media_results:
            media_cluster_builder.track_media(media)
        global media_clusters
        media_clusters = media_cluster_builder.get_sorted_clusters()
        data['center'] = {'lat': 37.813725, 'lng': -122.380526}
        data['time_spent'] = int(time.time() - now_timestamp_s)
        data['cluster_count'] = len(media_clusters)
        clusters = []
        for i in range(len(media_clusters)):
            media_cluster = media_clusters[i]
            # Get ML clusters.
            ml_clusters = MLServiceClient().get_ml_cluster(media_cluster)
            media_content = ''
            for media in media_cluster.media_list:
                media_content += _MEDIA_IMAGE_TEMPLATE.format(media.get('image_url').get('thumbnail_url'))
            # Generate ML cluster info.
            ml_cluster_info = ''
            if ml_clusters and len(ml_clusters) > 0:
                ml_cluster_content = ''
                for ml_cluster in ml_clusters:
                    ml_media_content = ''
                    for media in ml_cluster:
                        ml_media_content += _MEDIA_IMAGE_TEMPLATE.format(media.get('image_url').get('thumbnail_url'))
                    ml_cluster_content += _ML_CLUSTER_CONTENT_TEMPLATE.format(ml_media_content)
                ml_cluster_info = _ML_CLUSTER_INFO_TEMPLATE.format(len(ml_clusters), ml_cluster_content)
            cluster_info = _CLUSTER_INFO_TEMPLATE.format('/cluster/{0}'.format(i), media_cluster.media_count,
                                                         media_content, ml_cluster_info)
            clusters.append({
                'media_count': media_cluster.media_count,
                'url': '/cluster/{0}'.format(i),
                'center': media_cluster.cluster_center,
                'cluster_info': cluster_info})
        data['clusters'] = clusters
        return render_template('clusters.html', data=data)
    except:
        traceback.print_exc(file=sys.stdout)


@app.route('/cluster/<int:cluster_id>')
def display_cluster(cluster_id):
    try:
        global media_clusters
        media_cluster = media_clusters[cluster_id]
        ret = ''
        for media in media_cluster.media_list:
            caption = media.get('caption')
            if caption:
                caption = caption.encode('utf-8')
            ret += '<p><img src="{0}" />{1}, location: ({2}, {3}), timestamp: {4}</p>'.format(
                media.get('image_url').get('thumbnail_url'),
                caption,
                media.get('lat'),
                media.get('lng'),
                media.get('timestamp')
            )
        return ret
    except:
        traceback.print_exc(file=sys.stdout)

@app.route('/verify_clusters/<int:days_later>')
def verify_clusters_in_days(days_later):
    try:
        media_cluster_builder = MediaClusterBuilder(distance_mode=DistanceMode.PAIRWISE_ALL)
        
        now_timestamp_s = long(time.time())

        timestamp_s = 1431517522 + 60 * 60 * 24 * days_later
        timestamp_e = timestamp_s + 60 * 60 * 24
        media_results = mongo_client.search_media_by_time(timestamp_s, timestamp_e)
        data = dict()
        data['db_time_spent'] = int(time.time() - now_timestamp_s)
        for media in media_results:
            media_cluster_builder.track_media(media)
        global media_clusters
        media_clusters = media_cluster_builder.get_sorted_clusters()
        data['center'] = {'lat': 37.813725, 'lng': -122.380526}
        data['time_spent'] = int(time.time() - now_timestamp_s)
        data['cluster_count'] = len(media_clusters)
        clusters = []
        for i in range(len(media_clusters)):
            media_cluster = media_clusters[i]
            media_content = ''
            for media in media_cluster.media_list:
                media_content += _MEDIA_IMAGE_TEMPLATE.format(media.get('image_url').get('thumbnail_url'))
            cluster_info = _CLUSTER_INFO_TEMPLATE.format('/cluster/{0}'.format(i), media_cluster.media_count, media_content)
            clusters.append({
                'media_count': media_cluster.media_count,
                'url': '/cluster/{0}'.format(i),
                'center': media_cluster.cluster_center,
                'cluster_info': cluster_info})
        data['clusters'] = clusters
        return render_template('clusters.html', data=data)
    except:
        traceback.print_exc(file=sys.stdout)

@app.route('/label/<int:hours_later>')
def display_data(hours_later):
    try:
        timestamp_s = 1431517522 + 60 * 60 * hours_later
        timestamp_e = timestamp_s + 60 * 60 * 1
        media_results = mongo_client.search_media_by_time(timestamp_s, timestamp_e)
        #data = dict()
        #data['db_time_spent'] = int(time.time() - now_timestamp_s)
        ret = ''
        for media in media_results:
            caption = media.get('caption')
            if caption:
                caption = caption.encode('utf-8')
            #ret += '<p style="position: relative; max-width: 400; word-wrap: break-word; left: ' + str(min((float(media.get('latitude'))-37.775)*1000+30,80)) + '%">' + '<textarea>' + media.get('source_url') + '</textarea>' + '<img src="{0}" /><br/>{1}, location: ({2}, {3}), timestamp: {4}</p>'.format(
            ret += '<p><img src="{0}" />{1}, location: ({2}, {3}), timestamp: {4}</p>'.format(
                media.get('image_url').get('thumbnail_url'),
                caption,
                media.get('latitude'),
                media.get('longitude'),
                media.get('created_time')
            )
        return ret
    except:
        traceback.print_exc(file=sys.stdout)


if __name__ == '__main__':
    global media_clusters
    media_clusters = list()
    app.run()
