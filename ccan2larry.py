#!/usr/bin/env python3
import sys, requests
sys.path.append("/home/tokgeo/GitHub/ccan_viewer/")
from datetime import datetime
from bson.objectid import ObjectId
import xml.etree.ElementTree as XML
import json
from ccan_viewer import *

class CCAN2Larry(CCANViewer):
    larry_api = "https://frustrum.pictor.uberspace.de/larry/api"
    larry_entries = list()
    def __init__(self, app : QApplication):
        QMainWindow.__init__(self)
        self.app = app
        self.ui = False
    
    def toLarry(self):
        if not self.lsEntries:
            raise ValueError("No entries found or loaded")
        
        self.larry_entries = []
        
        for item in self.lsEntries:
            entry = item.ccan
            larry = LarryEntry()
            larry.ccan = entry
            larry.title = item.text()
            larry.author = entry["author"]
            larry.description = entry["description"]
            larry.updated_at = larry.created_at = entry["date"]
            larry.voting = round(entry["niveau"], 0)
            larry.dependencies = list()
            larry.tags = ["ccan"]
            larry.id["upload"] = larry.id["file"] = ObjectId.from_datetime(larry.updated_at)
            larry.id["author"] = ObjectId(entry["author"].encode("utf-8").ljust(12, b"\0")[:12])
            
            # print(f"Author: {larry.author}, ID: {larry.id['author']}")
            self.larry_entries.append(larry)
    
    def toXML(self):
        def link(root, title : str, href : str = ""):
            e_links = XML.SubElement(root, "_links")
            e_self = XML.SubElement(e_links, "self")
            XML.SubElement(e_self, "title").text = title
            XML.SubElement(e_self, "href").text = href
        
        def display_array(root, name : str, array : list):
            if not array:
                XML.SubElement(root, name)
            else:
                for i in array:
                    XML.SubElement(root, name).text = i
        
        output = ""
        root = XML.Element("uploads")
        link(root, "uploads")
        e_meta = XML.SubElement(root, "_meta")
        e_pagination = XML.SubElement(e_meta, "pagination")
        XML.SubElement(e_pagination, "total").text = str(len(self.larry_entries))
        XML.SubElement(e_pagination, "limit").text = str(len(self.larry_entries))
        XML.SubElement(e_pagination, "page").text = "1"
        XML.SubElement(e_pagination, "pages").text = "1"
        
        for entry in self.larry_entries:
            e_upload = XML.SubElement(root, "upload")
            e_upload.attrib["id"] = str(entry.id["upload"])
            link(e_upload, "Upload", str(entry.id["upload"]))
            
            XML.SubElement(e_upload, "uploadedAt").text = entry.updated_at.strftime("%Y-%m-%dT%H:%H:%SZ")
            XML.SubElement(e_upload, "createdAt").text =  entry.created_at.strftime("%Y-%m-%dT%H:%H:%SZ")
            XML.SubElement(e_upload, "slug").text = entry.slug
            
            e_author = XML.SubElement(e_upload, "author")
            XML.SubElement(e_author, "_id").text = str(entry.id["author"])
            XML.SubElement(e_author, "username").text = entry.author
            
            XML.SubElement(e_upload, "title").text = entry.title
            XML.SubElement(e_upload, "description").text = entry.description
            XML.SubElement(e_upload, "file").text = str(entry.id["file"])
            
            e_voting = XML.SubElement(e_upload, "voting")
            XML.SubElement(e_voting, "sum").text = str(entry.voting)
            
            display_array(e_upload, "dependency", entry.dependencies)
            display_array(e_upload, "tag", entry.tags)
        
        return XML.tostring(root, encoding="unicode")
    
    def dumpIDs(self):
        ids = {}
        for entry in self.larry_entries:
            ids[entry.ids["file"]] = larry.ccan["download_url"]
        
        with open("ids.json", "w") as fobj:
            json.dump(ids, fobj)
        

class LarryEntry(object):
    title = str()
    author = str()
    slug = str()
    description = str()
    
    id = {
        "upload" : ObjectId(),
        "file" : ObjectId(),
        "author" : ObjectId(),
        }
    
    updated_at = None
    created_at = None
    
    voting = int()
    
    dependencies = list()
    tags = list()
    ccan = dict()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    conv = CCAN2Larry(app)
    conv.fetchCCANList()
    conv.toLarry()
    conv.dumpIDs()
    print(conv.toXML())
