'''Wait until the configured database accepts connections.'''

import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Aguarda o banco de dados padrão aceitar conexões.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Tempo máximo de espera em segundos (default: 60).',
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=2.0,
            help='Intervalo entre tentativas em segundos (default: 2).',
        )

    def handle(self, *args, **options):
        timeout = options['timeout']
        interval = options['interval']
        if timeout < 0:
            raise CommandError('O timeout não pode ser negativo.')
        if interval <= 0:
            raise CommandError('O intervalo deve ser maior que zero.')

        deadline = time.monotonic() + timeout
        self.stdout.write('Aguardando o banco de dados...')

        while True:
            try:
                with connections['default'].cursor():
                    pass
            except OperationalError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CommandError(
                        f'Banco indisponível após {timeout}s.'
                    )
                time.sleep(min(interval, remaining))
            else:
                self.stdout.write(self.style.SUCCESS('Banco disponível.'))
                return
