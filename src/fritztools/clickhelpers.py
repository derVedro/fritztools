import click


class OrderedGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands


def split_params_commas_callback(ctx, param, values):
    # get rid of possible commas
    params = []
    for maybe_with_comma in values:
        param = maybe_with_comma.split(",")
        params.extend(param)
    return params
