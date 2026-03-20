from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import RestockTodo
from .serializers import RestockTodoSerializer


class RestockTodoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing restock todo items.
    Supports CRUD operations and custom status update action.
    """
    queryset = RestockTodo.objects.all()
    serializer_class = RestockTodoSerializer
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update status of a todo item.
        Accepts: { "status": "pending" | "completed" | "postponed" }
        """
        todo = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(RestockTodo.STATUS_CHOICES):
            return Response(
                {'error': f'Invalid status. Must be one of: {list(dict(RestockTodo.STATUS_CHOICES).keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        todo.status = new_status
        if new_status == 'completed':
            todo.completed_at = timezone.now()
        else:
            todo.completed_at = None
        todo.save()
        
        serializer = self.get_serializer(todo)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """
        Get todos filtered by status.
        Query param: status=pending|completed|postponed
        """
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = RestockTodo.objects.filter(status=status_filter)
        else:
            queryset = RestockTodo.objects.all()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
