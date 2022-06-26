from matplotlib import pyplot as plt


def trinomial_graph():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.spines['left'].set_position('center')
    ax.spines['bottom'].set_position('zero')
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')


def get_signal(coefs):
    letters = []
    for c in range(0, len(coefs)):
        if coefs[c][0] == 'n':
            letters.append(int(coefs[c][1:]) * (-1))
        else:
            letters.append(int(coefs[c]))
    return letters
