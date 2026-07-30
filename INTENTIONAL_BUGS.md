# Intentional bug catalogue

This file is an answer key for the person running the exercise. Keep it out of reach of testers until the session is over.

## API contract and validation

1. `GET /characters?offset=N` accepts `offset` but ignores it. The result always starts at the first character.
2. `POST /characters` accepts a `homeworld_id` that does not exist. The database relationship is broken, but the API returns `201`.
3. `PATCH /characters/{id}?side=anything` accepts any side, even though creation only documents `rebel`, `empire`, and `neutral`.
4. Creating a planet with an existing `name` produces an unhandled database error (`500`) rather than a client-friendly conflict response.

## Resource semantics

5. `DELETE /characters/{missing_id}` responds `204 No Content` rather than `404`.
6. `POST /missions` creates missions as `active`, although the model/database default says `planned` and a newly created mission is expected to begin planned.
7. `POST /missions` accepts an `assigned_to_id` for a non-existent character.
8. `PATCH /missions/{id}/status` permits invalid state jumps, such as `complete` back to `active` or `planned` straight to `complete`.
9. `PATCH /starships/{id}/fuel?level=N` accepts values outside the documented `0` to `100` fuel range, including negative values and values above `100`.

## Suggested probing

- Compare pagination results for `offset=0` and `offset=1`.
- Create a character or mission with a large bogus foreign-key ID, then retrieve it.
- Send a side such as `sith` to the character patch endpoint.
- Create the same planet twice and assert the response class and body.
- Repeat deletion of the same character.
- Exercise mission lifecycle transitions in varying orders.
- Set a starship's fuel to `-1`, `101`, and a very large integer; then retrieve it to confirm the value persisted.
