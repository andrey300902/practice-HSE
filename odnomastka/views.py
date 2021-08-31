from django.shortcuts import render
from .forms import MatrixForm, NameForm
import game

q = 0
res = None
text = []

def index(request):
    global q, res, text
    if q == 0:
        if request.method == 'POST':
            form = MatrixForm(request.POST)
            if form.is_valid():
                with open('settings.txt', 'w') as file:
                    lines = ['mode = Comp_vs_Comp\n', 'type = normal\n', 'user = 0\n', 'first_player = 0\n',
                             'vector = 01010110\n', 'k = 4\n', 'user_cards:\n', '0_cards: 1 2 5\n',
                             'weights: 1 1 1 1 1 1 1 1 1 1 1 1 1']
                    if form.cleaned_data['mode']:
                        lines[0] = 'mode = User_vs_Comp\n'
                    if form.cleaned_data['type']:
                        lines[1] = 'type = tiny\n'
                    lines[4] = 'vector = ' + form.cleaned_data['vector'] + '\n'
                    lines[5] = 'k = ' + str(len(form.cleaned_data['vector']) / 2) + '\n'
                    print(form.cleaned_data)
                    file.writelines(lines)
                res = game.Game()
                if not form.cleaned_data['mode']:
                    q = 1
                    text = res.Play()
                    x1 = text[2].split()
                    x2 = int(x1[1])
                    x1 = int(x1[0])
                    return render(request, 'play.html',
                                  {'user_card': res.vector0, 'other_card': res.vector1, 'user': False, 'text': text[0:2], 'x1': x1, 'x2': x2})
                q = 2
                return render(request, 'play.html', {'user_card': res.vector0, 'other_card': res.vector1, 'user': True, 'text': '', 'x1': 0, 'x2': 0})
        return render(request, 'index.html', {'form': [], 'flag_posted': False})
    elif q == 1:
        print(request.POST)
        if len(text) > 5:
            del text[0:3]
            x1 = text[2].split()
            x2 = int(x1[1])
            x1 = int(x1[0])
            return render(request, 'play.html',
                      {'user_card': res.vector0, 'other_card': res.vector1, 'user': False, 'text': text[0:2], 'x1': x1,
                       'x2': x2})
        else:
            x1 = text[-2].split()
            x2 = int(x1[1])
            x1 = int(x1[0])
            return render(request, 'play.html',
                          {'user_card': res.vector0, 'other_card': res.vector1, 'user': False, 'text': text[-1],
                           'x1': x1,
                           'x2': x2})

    else:
        if request.method == 'POST':
            try:
                form = NameForm(request.POST)
                print(1)
                print(form)
                move = form.cleaned_data['move']
                print(2)
                text = res.move(int(move))
                print(3)
                return render(request, 'play.html',
                          {'user_card': res.vector0, 'other_card': res.vector1, 'user': False, 'text': text,
                           'x1': res.x,
                           'x2': res.y})
            except:
                return render(request, 'play.html',
                              {'user_card': res.vector0, 'other_card': res.vector1, 'user': True, 'text': [],
                               'x1': res.x,
                               'x2': res.y})
            #text = res.Play()
        return render(request, 'play.html',
                      {'user_card': res.vector0, 'other_card': res.vector1, 'user': True, 'text': [],
                       'x1': res.x,
                       'x2': res.y})
