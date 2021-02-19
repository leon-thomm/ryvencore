# Convenience GUI Classes

Just a quick overview over the currently available convenience GUI classes. Meaning, all those classes only use ryvencore's public API and you could implement them all yourself. The list should grow over time. All these classes come from Ryven so far.

## Script List Widget

A simple list widget for creating, renaming and deleting scripts and function-scripts. To catch the according events (i.e. `script_created`, `script_renamed` etc), use the signals of `Session`.

## Variables List Widget

A synchronous widget to the script list widget for script variables. You can create, rename, delete script variables and change their values which results in all registered receivers to update.

## Log Widget

A very basic widget for outputting data of a log. Use the `Script.logger.new_log_created()` signal to catch instantiation of new logs. If you want to implement your own, you will need the `Log`'s signals `enabled`, `disabled`, `cleared`, `wrote`.

## Input Widgets

- `std line edit ` aka `std line edit m`, `std line edit s`, `std line edit l`
- `std spin box`

For styling those, refer to thir classes `RCIW_BUILTIN_LineEdit`, `RCIW_BUILTIN_SpinBox`.

I really would like to add many more widgets to this list in the future.