import matplotlib.pyplot as plt
from PIL import Image
import requests
from bs4 import BeautifulSoup
import re

pattern = re.compile("(\~\$.*?\$\~)+?")
patternOver = re.compile(".*\\\over.*")
patternOverLine = re.compile(".*\\\overline.*")
patternSqrt = re.compile(".*\\\sqrt(\[.*\])*.*")
patternSqrtSplit = re.compile("\\\sqrt\[.+\]|\\\sqrt")
latexPattern = re.compile("\{.*\}.*")
def parseTextToImg(res:list,url):
	index = 0
	indes = []
	print(res)
	for ls in res:
		if(ls[0]["type"]!="image"):
			choiceIndex = 0
			choice = ord('A')
			flag = False
			l = len(ls)
			d = 1 / (l + 1)
			fig = plt.figure(figsize=(7.1, 0.25 * l), facecolor='white')
			fig.clf()
			for x in range(l):
				each = ls[x]
				if(each!=""):
					if(not flag):
						if(each["type"]=="text"):
							text = each["text"]
						else:
							text = ""
					else:
						text = "  "+chr(choice+choiceIndex)+". "+each["text"]
						choiceIndex+=1
					text = text.replace(r"~", "")
					fig.text(0.02, 1-(d*x+d), text)
				else:
					flag = True
					fig.text(0.02, 1 - (d * x + d), "")
			plt.savefig(str(index)+".jpg")
			indes.append(str(index))
			index+=1
		else:
			response = requests.get(ls[0]["text"],verify=False)
			with open(str(index)+'.jpg', 'ab') as f:
				f.write(response.content)
				f.close()
			indes.append(str(index))
			index += 1
	combineImg(indes,url)

def cleanResult(question:list):
	result = []
	for each in question:
		if(each != "" and each["type"] == "text"):
			r =resolve_each(each["text"])
			result.extend(r)
		else:
			result.append(each)
	return result

def resolve_each(text:str):
	index = 0
	# TODO text = text.replace("\\over","/")
	ls = re.split(pattern,text)
	each_content = ""
	result = []
	for each in ls:
		if(re.match(pattern,each)is None):
			for word in each.split(" "):
				if(word == ""):
					continue
				elif(index + len(word) <= 90):
					index += len(word)+1
					each_content += " "+word
				else:
					result.append({"type":"text","text":each_content})
					each_content = word
					index = len(word)
		else:
			each = resolveOverCmd(each)
			each = resolveSqrtCmd(each)
			if(index + 4 <= 90):
				index += 4
				each_content += " "+each
			else:
				result.append({"type":"text","text":each_content})
				index = 4
				each_content = each
	result.append({"type":"text","text":each_content})
	return result

def resolveHtml(text:str):
	soup = BeautifulSoup(text,"lxml")
	result = []
	question = soup.find("div","question-content").find_all("p")
	for child in question:
		if(child.find("img")is not None):
			print(child.find("img"))
			result.append(generate(child.find("img").get("src"), "image"))
			if(len(child.text)>5):
				result.append(generate(child.text, "text"))
		else:
			result.append(generate(child.text,"text"))
	choice = soup.find_all("div","choice-content")
	result.append("")
	for each in choice:
		result.append(generate(each.find("p").text,"text"))
	return result

def splitResult(ls:list):
	result = []
	each_result = []
	for each in ls:
		if(each!="" and each["type"]=="image"):
			if(len(each_result)!=0):
				result.append(each_result)
				each_result = []
			result.append([each])
		else:
			each_result.append(each)
	if(len(each_result)>0):
		result.append(each_result)
	return result

def generate(text,type):
	return {"type":type,"text":text}

def combineImg(ls:list,url):
	r = []
	maxw = 0
	maxh = 0
	for each in ls:
		img = Image.open(each+".jpg")
		w,h = img.size
		maxh+=h
		if(w>maxw):
			maxw = w
		r.append(img)
	result = Image.new("RGB",(maxw,maxh),"white")
	high = 0
	for each in r:
		result.paste(each,box=(0,high))
		w,h = each.size
		high+=h

	result.save(url.split("/")[-1]+".jpg")

def runStart(url):
	response = requests.get(url)
	text = response.content
	result = resolveHtml(text)
	result = cleanResult(result)
	result = splitResult(result)
	parseTextToImg(result,url)

def resolveOverCmd(text):
	if(re.match(patternOver,text)is not None and re.match(patternOver,text)is None):
		text = text.replace("$","").replace("~","")
		ls = text.split(" ")
		str = ""
		length = len(ls)
		for i in range(length):
			each = ls[i]
			if(each!="\\over"):
				str += each
			else:
				str = "~$\\frac{"+str+"}{"
		str += "}$~"
		return str
	else:
		return text

def resolveSqrtCmd(text:str):
	if(re.match(patternSqrt,text)is not None):
		text = text.replace("$","").replace("~","").strip()
		str = ""
		ls = re.split(patternSqrtSplit,text)
		sqs = re.findall(patternSqrtSplit,text)
		for i in range(len(ls)):
			if(i == 0):
				str = ls[i]
			elif(i>0):
				if(re.match(latexPattern,ls[i])):
					str += sqs[i-1]+ls[i]
				else:
					str += sqs[i - 1] + "{" + ls[i] + "}"
		return "~$"+str+"$~"
	return text


if __name__ == '__main__':
	# print(len(""))
	# response = requests.get("https://gmat.la/question/OG2018Q-DS-291")
	runStart("https://gmat.la/question/OG2018Q-DS-216")
	# result = [{"type":"text","text":"~$5\\sqrt[3]q$~"}]
	# result = cleanResult(result)
	# result = splitResult(result)
	# parseTextToImg(result, "22")
	# print(re.split(patternSqrtSplit,"~$ 5\\sqrt[3]q$~"))
	# print(re.match(latexPattern,"{q}$~"))
	# print(re.split(patternSqrtSplit, "~$ 5\\sqrtq$~"))
