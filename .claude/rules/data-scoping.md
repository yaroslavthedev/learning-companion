# Data scoping rules (always apply)

A user must never see, change or even detect another user's data.

- Every view that returns user data needs login (`LoginRequiredMixin` /
  `login_required`).
- Every queryset in a view starts from the current user:
  - `Goal.objects.filter(owner=self.request.user)`
  - `LearningSession.objects.filter(goal__owner=self.request.user)`
  - `Resource.objects.filter(goal__owner=self.request.user)`
  - `Tag.objects.filter(owner=self.request.user)`
- Never `Model.objects.get(pk=...)` or `.all()` in a view. Use
  `get_object_or_404(<scoped queryset>, pk=...)`.
- Another user's object → **404** (not 403, not a redirect).
- The owner is set on the server (`form.instance.owner = self.request.user`),
  never taken from a form field or URL.
- Form choice fields (goal picker, tag picker) list only the user's own objects:
  restrict `queryset` in the form's `__init__`.
- AI prompts and dashboard aggregations use the same scoped querysets.
- Every detail / update / delete view has a test where user B requests user A's
  object and gets 404. Every list view has a test that B doesn't see A's rows.
- Rows linking two user-owned objects (session ↔ tags, session ↔ goal) must
  share one owner. Enforce it wherever the link can be set: app forms *and* admin.
- Admin for user-owned models: FK/M2M fields pointing at other user-owned
  models are read-only or use `autocomplete_fields`; never a plain picker of
  every user's rows. Add `list_select_related` for FKs in `list_display`.
