from rules import rules as main_rules


class Level(object):
    def __init__(self, rules):
        self.rules = rules

    def start(self):
        for key, rule in self.rules.iteritems():
            setattr(main_rules, key, rule)

    def next_std_level(self):
        new_rules = self.rules.copy()
        new_rules['enemy_generation_speed'] /= 1.8
        new_rules['enemy_speed'] /= 1.1
        return Level(new_rules)

levels = [
    Level({
        'enemy_generation_speed': 0.05,
        'enemy_speed': 14.0,
        'bullet_shooting_speed': 0.05,
        'dropout_generation_cons_pause': 4.0,
        'dropout_generation_rand_pause': 4.0,
    }),
    Level({
        'enemy_generation_speed': 0.04,
        'enemy_speed': 12.0,
        'bullet_shooting_speed': 0.05,
        'dropout_generation_cons_pause': 3.0,
        'dropout_generation_rand_pause': 4.0,
    }),
    Level({
        'enemy_generation_speed': 0.03,
        'enemy_speed': 15.0,
        'bullet_shooting_speed': 0.04,
        'dropout_generation_cons_pause': 3.0,
        'dropout_generation_rand_pause': 3.0,
    }),
    Level({
        'enemy_generation_speed': 0.02,
        'enemy_speed': 12.0,
        'bullet_shooting_speed': 0.04,
        'dropout_generation_cons_pause': 3.0,
        'dropout_generation_rand_pause': 3.0,
    }),
]
