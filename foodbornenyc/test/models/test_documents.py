import pytest
from mock import Mock, patch

import json
import foodbornenyc.sources.twitter_search as twitter_search
from foodbornenyc.models.businesses import Business
from foodbornenyc.models.locations import Location
from foodbornenyc.models.documents \
    import Document, DocumentAssoc, Tweet, YelpReview
from foodbornenyc.test.test_db import clear_tables, get_db_session

@pytest.fixture(scope="function")
def db():
    clear_tables()
    return get_db_session()

def test_Document(db):
    """ Document and DocumentAssoc onstruction should work"""
    sample_id = '123'
    assoc = DocumentAssoc(sample_id, "tweet");
    document = Document(sample_id)
    document.assoc_id = sample_id
    db.add_all([document, assoc])
    db.commit()
    assert db.query(Document).first().id == sample_id
    assert db.query(DocumentAssoc).first().assoc_id == sample_id

def testYelpReview(db):
    """ YelpReview construction should work, including creating Documents """
    sample_business = {'business_id':3, 'name':'Foodborne'}
    sample = {'yelp_id': '14', 'rating': 4, 'text': "Nice!", 'user_name': "joe"}

    business = Business(**sample_business)
    review = YelpReview(**sample)
    review.business_id = sample_business['business_id']
    db.add(business)
    db.add(review)
    db.commit()

    # test immediate fields
    review = db.query(YelpReview).first()
    assert review.id == sample['yelp_id']
    assert review.text == sample['text']
    assert review.rating == sample['rating']
    assert review.user_name == sample['user_name']

    # test document
    assert review.document_rel.assoc_id == sample['yelp_id']
    assert review.document.id == review.document_rel.document[0].id

def testTweet(db):
    """ Tweet construction should work, including creating documents """
    sample = { 'id_str':'2', 'text':"I hate food!",
               'in_reply_to_user_id_str': '233', 'lang': 'en',
               'in_reply_to_status_id_str': '449' }
    sample_optional = { 'user': {'id_str': '234'},
                        'location': Location(line1='11 Main St', city='Boston'),
                        'created_at': 'Tue Feb 23 23:40:54 +0000 2015' }

    sample2 = sample.copy()
    sample2.update(sample_optional)

    db.add(Tweet(**sample))
    db.commit()

    # test immediate fields
    tweet = db.query(Tweet).first()
    assert tweet.id == sample['id_str']
    assert tweet.user_id == None
    assert tweet.created_at == None
    assert tweet.location == None
    assert tweet.text == sample['text']
    assert tweet.in_reply_to_user_id_str == sample['in_reply_to_user_id_str']
    assert tweet.lang == sample['lang']
    assert tweet.in_reply_to_status_id_str == \
        sample['in_reply_to_status_id_str']

    # test optinal fields
    db.delete(tweet)
    db.add(Tweet(**sample2))
    db.commit()

    tweet = db.query(Tweet).first()
    assert tweet.location == sample2['location']
    assert tweet.user_id == sample2['user']['id_str']

    # test document
    assert tweet.document_rel.assoc_id == sample['id_str']
    assert tweet.document.id == tweet.document_rel.document[0].id
