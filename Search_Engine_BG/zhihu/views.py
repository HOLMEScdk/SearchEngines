from django.shortcuts import render
from django.shortcuts import HttpResponse

# Create your views here.
from search_engine import generate_graph
import jieba
import re
import json
from search_engine import Rules
jieba.load_userdict('./search_engine/user_name.txt')


def search(request):
    res_dict = dict()
    if request.method == 'GET':
        text = request.GET.get('') # input name
        cut = jieba.cut_for_search(text)
        joint_cut = ','.join(cut)
        list_text = [x for x in re.split(r'[\s!@%^,;\n]',joint_cut) if x]  # 测试数据
        flag, name, kind = Rules.judge_rule(list_text)  # 划分
        if name is None or flag == 0:
            return HttpResponse(json.dumps({'NONE': True}))
        if flag == 1:  # 层次图
            res_dict = generate_graph.get_graph('user', name)
        elif flag == 2:
            pass
        elif flag == 3:
            pass
        if res_dict is None:
            return HttpResponse(json.dumps({'NONE': True}))
        return HttpResponse(json.dumps(res_dict))
    return render(request, 'index.html')
