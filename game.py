import copy
import time

pow2 = [0] * 51
pow2[0] = 1
for i in range(1, 51):
    pow2[i] = pow2[i - 1] * 2


def create_mask(vector):
    mask = 0
    for i in range(len(vector)):
        mask = mask * 2 + vector[i]
    return mask


def move_mask(mask, i, j):
    if (j > i):
        i, j = j, i
    mask = (mask // (pow2[i + 1])) * pow2[i] + (mask % pow2[i])
    return (mask // (pow2[j + 1])) * pow2[j] + (mask % pow2[j])


def make_vector(mask):
    vector = []
    while (mask > 0):
        vector.append(mask % 2)
        mask //= 2
    vector.reverse()
    return vector


def pl(mask, i):
    return (mask // pow2[i]) % 2


class Position:
    def __init__(self, vector=None, ip=None, mot=None, bribe=None):
        self.k = [0] * 2
        self.x = 0
        self.curr_player = 0
        self.table = -1
        if ip is None:
            self.size = len(vector)
            self.mask = create_mask(vector)
        else:
            self.size = ip.size - 2
            self.mask = move_mask(ip.mask, ip.size - ip.table - 1, ip.size - mot - 1)
            i = ip.curr_player
            j = (ip.curr_player + 1) % 2
            if mot > ip.table:
                self.curr_player = i
                self.x = bribe
                self.k[i] = ip.k[i] + bribe
                self.k[j] = ip.k[j]
            else:
                self.curr_player = j
                self.x = -bribe
                self.k[i] = ip.k[i]
                self.k[j] = ip.k[j] + bribe

            if (ip.curr_player == 1):
                self.x *= -1


class InterPosition:
    def __init__(self, p, mot):
        self.size = p.size
        self.mask = p.mask
        self.x = 0
        self.k = copy.copy(p.k)
        self.curr_player = (p.curr_player + 1) % 2
        self.table = mot


f = {}
optimal_moves = {}
better_beat = {}
better_skip = {}
can_beat = {}
can_skip = {}
takings = {}
skippings = {}
best_mot = {}
bad_moves = {}

MAX_CONST = 10000
MIN_CONST = -10000


class DeepGreen:
    def __init__(self):
        self.type = 'normal'
        self.K = 0
        self.a = 0
        self.b = 1
        self.card = []
        self.mode = 'normal'
        self.weights = []

    def h(self, p):
        return (p.mask, p.curr_player, p.table)

    def g(self, p):
        if self.h(p) in f:
            return f[self.h(p)] + p.x
        if p.size == 0:
            return p.x
        return MIN_CONST

    def less(self, a, b):
        if self.type == 'normal':
            return a < b
        else:
            return a > b

    def greater(self, a, b):
        if self.type == 'normal':
            return a > b
        else:
            return a < b

    def Range(self, n):
        if self.type == 'normal':
            return range(n)
        else:
            return range(n - 1, -1, -1)

    def change_type_to_tiny(self):
        global MAX_CONST, MIN_CONST
        self.type = 'tiny'
        MAX_CONST, MIN_CONST = MIN_CONST, MAX_CONST

    def AddInterPositionPreview(self, ip, poss_moves):
        if self.type == 'tiny' or self.mode == 'weights':
            return

        better_beat[self.h(ip)] = True
        better_skip[self.h(ip)] = True
        can_beat[self.h(ip)] = False
        can_skip[self.h(ip)] = False
        for [i, g] in poss_moves:
            if i > ip.table:
                can_beat[self.h(ip)] = True
                if g == f[self.h(ip)]:
                    better_skip[self.h(ip)] = False
            else:
                can_skip[self.h(ip)] = True
                if g == f[self.h(ip)]:
                    better_beat[self.h(ip)] = False

    def AddPositionPreview(self, p, poss_moves):
        if self.type == 'tiny' or self.mode == 'weights':
            return

        bad_moves[self.h(p)] = 0
        for move in poss_moves:
            if move > f[self.h(p)]:
                bad_moves[self.h(p)] += 1

    def find_best_mot(self, p):
        if self.type == 'tiny':
            return optimal_moves[self.h(p)][0]
        elif self.mode == 'weights' or len(optimal_moves[self.h(p)]) == 1:
            return optimal_moves[self.h(p)][0]
        elif p.table != -1:
            b = Position([], p, optimal_moves[self.h(p)][0], 1)
            if bad_moves[self.h(b)] > b.size / 10:
                return optimal_moves[self.h(p)][0]
            else:
                return optimal_moves[self.h(p)][1]
        else:
            takings[self.h(p)] = []
            skippings[self.h(p)] = []
            prev = -100
            b = InterPosition(p, optimal_moves[self.h(p)][0])
            for mot in optimal_moves[self.h(p)]:
                if mot != prev + 1:
                    b = InterPosition(p, mot)
                if (better_beat[self.h(b)]) and (can_skip[self.h(b)]):
                    skippings[self.h(p)].append(mot)
                elif (better_skip[self.h(b)]) and (can_beat[self.h(b)]):
                    takings[self.h(p)].append(mot)
                prev = mot

            if (len(takings[self.h(p)]) != 0) and (len(skippings[self.h(p)]) != 0):
                if p.size - 1 - skippings[self.h(p)][-1] < takings[self.h(p)][0]:
                    return skippings[self.h(p)][-1]
                else:
                    return takings[self.h(p)][0]
            elif len(takings[self.h(p)]) != 0:
                return takings[self.h(p)][0]
            elif len(skippings[self.h(p)]) != 0:
                return skippings[self.h(p)][-1]
            else:
                return optimal_moves[self.h(p)][0]

    def AlternInterPositionPreviewWeights(self, ip, bribe):
        poss_moves = []
        m = MIN_CONST
        step = 0
        prev = -100
        prev_g = 0
        for i in self.Range(ip.size):
            if pl(ip.mask, ip.size - i - 1) != 0:
                continue

            elif abs(i - prev) == 1:
                poss_moves.append([i, prev_g])
                prev = i
                continue

            v = Position([], ip, i, bribe)
            self.PositionPreview(v, m - v.x)  # bound = m - v.x - ходы с меньшим итогом недопустимы

            if (self.g(v) == MIN_CONST):
                continue

            poss_moves.append([i, self.g(v)])
            if self.greater(self.g(v), m):
                m = self.g(v)
                step = i

            prev = i
            prev_g = self.g(v)

        f[self.h(ip)] = m
        optimal_moves[self.h(ip)] = [step]

        for move in poss_moves:
            if (move[1] == m and move[0] != step):
                optimal_moves[self.h(ip)].append(move[0])

        best_mot[self.h(ip)] = self.find_best_mot(ip)

    def InterPositionPreview(self, ip, bound):
        if (self.h(ip) in f):
            # print('Old InterPosition', 'mask:', make_vector(ip.mask), 'key = ', self.h(ip), 'x=', ip.x, 'f=',
            # f[self.h(ip)], 'g=', self.g(ip))
            return

        bribe = self.weights[self.K - ip.size // 2]

        if ip.curr_player == 0:
            if self.mode == 'weights':
                self.AlternInterPositionPreviewWeights(ip, bribe)
                return

            Min = MAX_CONST
            MinUpTable = MAX_CONST
            for i in self.Range(ip.size):
                if pl(ip.mask, ip.size - i - 1) != 0:
                    continue

                if self.less(i, Min):
                    Min = i
                if self.less(i, MinUpTable) and self.greater(i, ip.table):
                    MinUpTable = i

            # 1)
            p1 = Position([], ip, Min, bribe)
            self.PositionPreview(p1, MIN_CONST)
            f[self.h(ip)] = self.g(p1)
            optimal_moves[self.h(ip)] = [Min]

            # 2)
            if MinUpTable != MAX_CONST and MinUpTable != Min:
                p2 = Position([], ip, MinUpTable, bribe)
                self.PositionPreview(p2, f[self.h(ip)] - p2.x)  # bound = f[self.h(ip)] - p2.x
                # - Текущее значение ф-ии
                if self.greater(self.g(p2), f[self.h(ip)]):
                    f[self.h(ip)] = self.g(p2)
                    optimal_moves[self.h(ip)][0] = MinUpTable
                elif self.g(p2) == f[self.h(ip)]:
                    if self.type == 'normal':
                        optimal_moves[self.h(ip)].append(MinUpTable)
                    else:
                        optimal_moves[self.h(ip)] = [MinUpTable, Min]

            best_mot[self.h(ip)] = self.find_best_mot(ip)

            # print('InterPosition, 0 mot:', 'mask:', make_vector(ip.mask), 'key = ', self.h(ip), 'x=', ip.x, 'f=', f[self.h(ip)], 'g=', self.g(ip))

        else:
            m = MAX_CONST
            step = -100
            poss_moves = []
            for i in self.Range(ip.size):
                if pl(ip.mask, ip.size - i - 1) != 1:
                    continue

                v = Position([], ip, i, bribe)
                self.PositionPreview(v, MIN_CONST)

                if self.less(self.g(v), bound):
                    return

                poss_moves.append([i, self.g(v)])

                if self.less(self.g(v), m):
                    m = self.g(v)
                    step = i

            f[self.h(ip)] = m
            self.AddInterPositionPreview(ip, poss_moves)

            # print('InterPosition, 1 mot:', 'mask:', make_vector(ip.mask), 'key = ', self.h(ip), 'x=', ip.x, 'f=', f[self.h(ip)], 'g=', self.g(ip))

    def PositionPreview(self, p, bound):
        if (self.h(p) in f):
            # print('Old Position', 'mask:', make_vector(p.mask), 'key = ', self.h(p), 'x=', p.x, 'f=', f[self.h(p)],
            # 'g=', self.g(p))
            return

        if p.size == 0:
            # print('End Position:', 'mask:', make_vector(p.mask), 'key = ', self.h(p), 'g=', self.g(p))
            return

        if p.curr_player == 0:
            poss_moves = []
            m = MIN_CONST
            step = 0
            prev = -100
            prev_g = 0
            for i in self.Range(p.size):
                if pl(p.mask, p.size - i - 1) != 0:
                    continue

                elif abs(i - prev) == 1:
                    poss_moves.append([i, prev_g])
                    prev = i
                    continue

                b = InterPosition(p, i)
                self.InterPositionPreview(b, m)  # bound = m - ходы с меньшим итогом недопустимы
                if (self.g(b) == MIN_CONST):
                    continue

                poss_moves.append([i, self.g(b)])
                if self.greater(self.g(b), m):
                    m = self.g(b)
                    step = i

                prev = i
                prev_g = self.g(b)

            f[self.h(p)] = m
            optimal_moves[self.h(p)] = [step]

            for move in poss_moves:
                if (move[1] == m and move[0] != step):
                    optimal_moves[self.h(p)].append(move[0])

            best_mot[self.h(p)] = self.find_best_mot(p)

            # print('Position, 0 mot:', 'mask:', make_vector(p.mask), 'key = ', self.h(p), 'x=', p.x, 'f=', f[self.h(p)], 'g=', self.g(p))

        else:
            poss_moves = []
            m = MAX_CONST
            prev = -100
            for i in self.Range(p.size):
                if pl(p.mask, p.size - i - 1) != 1:
                    continue

                b = InterPosition(p, i)
                self.InterPositionPreview(b, MIN_CONST)

                if self.less(self.g(b), bound):
                    return

                if abs(i - prev) != 1:
                    poss_moves.append(self.g(b))

                if self.less(self.g(b), m):
                    m = self.g(b)

                prev = i

            f[self.h(p)] = m
            self.AddPositionPreview(p, poss_moves)

            # print('Position, 1 mot:', 'mask:', make_vector(p.mask), 'key = ', self.h(p), 'x=', p.x, 'f=', f[self.h(p)], 'g=', self.g(p))

    def PrintAddInf(self, p):
        if len(optimal_moves[self.h(p)]) == 1:
            print('Других оптимальных ходов нет |', end=' ')
        else:
            print('Все оптимальные ходы:', end=' ')
            for i in optimal_moves[self.h(p)]:
                print(self.card[i], end=' ')
            print('| ', end='')

        if self.h(p) in takings:
            if len(takings[self.h(p)]) == 0:
                print('Взятий нет |', end=' ')
            else:
                print('Взятия:', end=' ')
                for i in takings[self.h(p)]:
                    print(self.card[i], end=' ')
                print('| ', end='')

            if len(skippings[self.h(p)]) == 0:
                print('Пропусканий нет |', end=' ')
            else:
                print('Пропускания:', end=' ')
                for i in skippings[self.h(p)]:
                    print(self.card[i], end=' ')
                print('| ', end='')

        delta = p.k[0] - p.k[1] + f[self.h(p)]
        if self.mode == 'normal':
            print('Ожидаемое кол-во взяток у ', self.a, ': ', (self.K + delta) // 2, sep='', end=' | ')
            print('Ожидаемое кол-во взяток у ', self.b, ': ', (self.K - delta) // 2, sep='')
        else:
            w_sum = sum(self.weights)
            print('Ожидаемая сумма взяток у ', self.a, ': ', (w_sum + delta) // 2, sep='', end=' | ')
            print('Ожидаемая сумма взяток у ', self.b, ': ', (w_sum - delta) // 2, sep='')

    def Start(self, vector, first_player=0):
        for i in range(len(vector)):
            self.card.append(i + 1)

        p = Position(vector)
        p.curr_player = first_player
        self.p = p
        self.PositionPreview(p, MIN_CONST)

    def move(self, x):
        if x == 4:
            q = 5
        p = self.p
        user_mot = self.card.index(x)
        ip = InterPosition(p, user_mot)
        comp_mot = best_mot[self.h(ip)]
        text = ['Ход ' + str(self.a) + ': ' + str(self.card[comp_mot])]
        self.PrintAddInf(ip)
        bribe = self.weights[self.K - ip.size // 2]
        p = Position([], ip, comp_mot, bribe)
        try:
            self.vector0.pop(self.vector0.index(x))
        except:
            self.vector0.pop(self.vector0.index(self.card[comp_mot]))
        try:
            self.vector1.pop(self.vector1.index(x))
        except:
            self.vector1.pop(self.vector1.index(self.card[comp_mot]))
        if self.card[comp_mot] > self.card[user_mot]:
            self.y += 1
        else:
            self.x += 1
        self.card.pop(max(comp_mot, user_mot))
        self.card.pop(min(comp_mot, user_mot))
        return text

    def print_cards(self, vector):
        kit0 = []
        kit1 = []
        for i in range(len(vector)):
            card = i + 1
            if (vector[i] + self.a) % 2 == 0:
                kit0.append(card)
            else:
                kit1.append(card)
        self.vector0 = kit0
        self.vector1 = kit1

    def read_vector(self, str):
        vector = []
        for c in str:
            if c == ' ':
                continue
            vector.append((int(c) + self.a) % 2)
        if len(vector) % 2 != 0:
            print('MISTAKE!')
            return
        self.K = len(vector) // 2
        return vector

    def Game(self, lines):  # считываем настройки из файла
        l = lines[1].split(' ')
        if l[2] != 'normal':
            self.change_type_to_tiny()
        l = lines[2].split(' ')
        self.b = int(l[2])  # игрок за которого играет user
        self.a = (self.b + 1) % 2  # игрок за которого играет комп
        l = lines[3].split(' ')
        first_player = (int(l[2]) + self.a) % 2

        vector = []
        l = lines[4].split()
        if len(l) > 2:
            vector = self.read_vector(lines[4][8:])
        else:
            l = lines[5].split()
            self.K = int(l[2])
            user_kit = set(map(int, lines[6][11:].split()))
            if (len(user_kit) != self.K):
                print('MISTAKE!')
                return
            for i in range(2 * self.K):
                y = 0
                if (i + 1) in user_kit:
                    y = 1
                vector.append(y)
        print('Двоичный вектор:', *[(y + 1) % 2 for y in vector])

        l = lines[8].split(' ')
        if len(l) > 1:
            self.weights = list(map(int, lines[8][8:].split()))
            self.mode = 'weights'
        else:
            self.weights = [1] * self.K
        self.print_cards(vector)
        self.x = 0
        self.y = 0
        self.Start(vector, first_player)

class CompWithCompGame:
    def __init__(self):
        self.player0 = DeepGreen()
        self.player0.a, self.player0.b = 0, 1
        self.player1 = DeepGreen()
        self.player1.a, self.player1.b = 1, 0
        self.K = 0
        self.card = []

    def Play(self):
        first_player = 0
        vector0 = self.vector
        vector1 = []
        for i in vector0:
            if i == 0:
                vector1.append(1)
            else:
                vector1.append(0)
        for i in range(len(vector0)):
            self.card.append(i + 1)

        self.player0.card = self.card
        self.player1.card = self.card

        p0 = Position(vector0)
        p0.curr_player = first_player
        p1 = Position(vector1)
        p1.curr_player = (p0.curr_player + 1) % 2

        self.player0.PositionPreview(p0, MIN_CONST)
        self.player1.PositionPreview(p1, MIN_CONST)
        text = []
        for i in range(self.K):
            if p0.curr_player == 0:
                mot0 = best_mot[self.player0.h(p0)]
                text.append('Ход 0: ' + str(self.card[mot0]))
                self.player0.PrintAddInf(p0)

                ip0 = InterPosition(p0, mot0)
                ip1 = InterPosition(p1, mot0)

                mot1 = best_mot[self.player1.h(ip1)]
                text.append('Ход 1: ' + str(self.card[mot1]))
                self.player1.PrintAddInf(ip1)
                bribe = self.player0.weights[self.K - ip0.size // 2]
                p0 = Position([], ip0, mot1, bribe)
                p1 = Position([], ip1, mot1, bribe)
                text.append(str(p0.k[0]) + ' ' + str(p0.k[1]))
                self.card.pop(max(mot0, mot1))
                self.card.pop(min(mot0, mot1))
            else:
                mot1 = best_mot[self.player1.h(p1)]
                text.append('Ход 1: ' + str(self.card[mot1]))
                self.player1.PrintAddInf(p1)

                ip0 = InterPosition(p0, mot1)
                ip1 = InterPosition(p1, mot1)

                mot0 = best_mot[self.player0.h(ip0)]
                self.player0.PrintAddInf(ip0)
                bribe = self.player0.weights[self.K - ip0.size // 2]
                p0 = Position([], ip0, mot0, bribe)
                p1 = Position([], ip1, mot0, bribe)
                text.append('Ход 0: ' + str(self.card[mot0]))
                text.append(str(p0.k[0]) + ' ' + str(p0.k[1]))
                self.card.pop(max(mot0, mot1))
                self.card.pop(min(mot0, mot1))

        if self.player0.greater(p0.k[0], p0.k[1]):
            text.append('0 Победил!')
        elif p0.k[0] == p0.k[1]:
            text.append('НИЧЬЯ')
        else:
            text.append('1 Победил!')
        return text

    def Game(self, lines):
        l = lines[1].split(' ')
        if l[2] != 'normal':
            self.player0.change_type_to_tiny()
            self.player1.type = 'tiny'
        l = lines[3].split(' ')
        first_player = int(l[2])

        vector0 = []
        vector1 = []
        l = lines[4].split()
        if len(l) > 2:
            vector0 = self.player0.read_vector(lines[4][8:])
            vector1 = self.player1.read_vector(lines[4][8:])
            self.K = self.player0.K
        else:
            l = lines[5].split()
            self.K = int(l[2])
            self.player0.K = self.K
            self.player1.K = self.K
            kit0 = set(map(int, lines[7][8:].split()))
            print(kit0)
            if (len(kit0) != self.K):
                print('MISTAKE!')
                return
            for i in range(2 * self.K):
                if (i + 1) in kit0:
                    vector0.append(0)
                    vector1.append(1)
                else:
                    vector0.append(1)
                    vector1.append(0)
        print('Двоичный вектор:', *vector0)

        l = lines[8].split(' ')
        if len(l) > 1:
            self.player0.weights = list(map(int, lines[8][8:].split()))
            self.player1.weights = self.player0.weights
            self.player0.mode = 'weights'
            self.player1.mode = 'weights'
        else:
            self.player0.weights = [1] * self.K
            self.player1.weights = self.player0.weights

        self.player0.print_cards(vector0)
        self.vector = vector0
        self.vector0 = []
        self.vector1 = []
        for i in range(len(vector0)):
            if vector0[i] == 0:
                self.vector0.append(i + 1)
            else:
                self.vector1.append(i + 1)


#        self.Play(vector0, vector1, first_player)


def Game():
    f = open('settings.txt', 'r')
    lines = [line.strip() for line in f]
    f.close()
    l = lines[0].split()
    if l[2] == 'Comp_vs_Comp':
        cwc = CompWithCompGame()
        cwc.Game(lines)
        return cwc
    else:
        dg = DeepGreen()
        dg.Game(lines)
        return dg

Game()
# 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0
