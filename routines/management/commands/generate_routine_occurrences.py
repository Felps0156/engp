'''Generate dated occurrences for active weekly routine items.'''

from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from routines.services import generate_routine_occurrences
from tenants.models import Workspace


def _parse_date(value, label):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CommandError(f'{label} deve estar no formato AAAA-MM-DD.') from exc


class Command(BaseCommand):
    help = 'Gera ocorrências idempotentes para itens de rotina ativos.'

    def add_arguments(self, parser):
        today = timezone.localdate().isoformat()
        parser.add_argument(
            '--start',
            default=today,
            help='Data inicial no formato AAAA-MM-DD (padrão: hoje).',
        )
        parser.add_argument(
            '--end',
            default=None,
            help='Data final no formato AAAA-MM-DD (padrão: igual à inicial).',
        )
        parser.add_argument(
            '--workspace-id',
            type=int,
            default=None,
            help='Limita a geração a um workspace ativo.',
        )

    def handle(self, *args, **options):
        start_date = _parse_date(options['start'], 'A data inicial')
        end_date = (
            _parse_date(options['end'], 'A data final')
            if options['end']
            else start_date
        )
        if end_date < start_date:
            raise CommandError('A data final não pode ser anterior à data inicial.')

        workspace = None
        workspace_id = options.get('workspace_id')
        if workspace_id is not None:
            try:
                workspace = Workspace.objects.get(
                    pk=workspace_id,
                    is_active=True,
                )
            except Workspace.DoesNotExist as exc:
                raise CommandError('Workspace ativo não encontrado.') from exc

        try:
            created_count = generate_routine_occurrences(
                start_date=start_date,
                end_date=end_date,
                workspace=workspace,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        scope = f' no workspace {workspace.pk}' if workspace else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{created_count} ocorrência(s) criada(s) de '
                f'{start_date:%d/%m/%Y} a {end_date:%d/%m/%Y}{scope}.'
            ),
        )
