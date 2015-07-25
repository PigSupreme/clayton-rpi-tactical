# -*- coding: utf-8 -*-
"""Module containing basic FSM functionality.

All states should be derived from the State class, see its documentation.

Use STATE_NONE as a concrete null state. We need only a single instance.

An instance of BaseEntity can be given FSM functionality as follows:

* fsm = StateMachine(entity)
* fsm.set_state(current, global, previous), the last two are optional
* entity.fsm = fsm
* In entity's update() method, call self.fsm.update()

In entity's receive_msg() method, calling entity.fsm.handle_msg(message) will
allow the FSM to route messages to the appropriate state logic: first to the
current state, then to the global state.

"""

class State(object):
    """Base class for all states.

    States derived from this base class should override the methods below,
    though all of them are optional. Each method takes a parameter, agent,
    which is the BaseEntity that is using that state. This allows multiple
    entities to reuse the same state logic.
    """
    def enter(self, agent):
        """Code to execute immediately when changing to this state."""
        pass

    def execute(self, agent):
        """Code to execute each time this state is executed."""
        pass

    def leave(self, agent):
        """Code to execute just before changing from this state."""
        pass

    def on_msg(self, agent, message):
        """Code to execute when a message is received.

            Note
            ----
            When overriding this method, we need to return a boolean that
            indicates if the message was succesfully handled. The messaging
            functions use this boolean to redirect the message elsewhere if a
            given state is unable to handle it.
        """
        return False # This means the message wasn't handled

STATE_NONE = State()
"""Use this as a concrete null state; we need only a single instance."""

class StateMachine(object):
    """Finite State Machine with messaging capability.

    After instantiating a new StateMachine, use the set_state() method below
    in order to explicity initialize the states. Otherwise, this FSM will sit
    around and do nothing on update.

    Parameters
    ----------
    owner: BaseEntity
        The entity using this instance of the FSM.
    """

    def __init__(self, owner):
        self.owner = owner
        self.cur_state = None
        self.glo_state = None
        self.pre_state = None

    def set_state(self, cur, glo=None, pre=None):
        """Manually set owner's states without triggering state change logic.

        Parameters
        ----------
        cur : State
            Current State of the FSM. Use NullState here if you don't need
            to explictly set an actual State.
        glo : State
            Global State (executed each update) of the FSM.
        pre : State
            Previous State (used by revert_state) of the FSM. Defaults to
            NullState if not specified or invalid.
        """
        self.cur_state = cur
        self.glo_state = glo
        if pre:
            self.pre_state = pre
        else:
            self.pre_state = STATE_NONE

    def start(self):
        """Start the FSM by executing global & current state's enter() methods.

        Note
        ----
        This is an attempt to fix the issue of BaseEntities not having access
        to messaging during their __init__() functions. This calls the enter()
        methods of the global state first, then the FSM's current state.
        """
        if self.glo_state:
            self.glo_state.enter(self.owner)
        if self.cur_state:
            self.cur_state.enter(self.owner)

    def update(self):
        """Execute the owner's global state (if any), then current state."""
        # First execute a global state if it exists
        if self.glo_state:
            self.glo_state.execute(self.owner)
        # Now execute the regular current state
        if self.cur_state:
            self.cur_state.execute(self.owner)

    def change_state(self, newstate):
        """Switches owner to a new state, calling leave/enter methods.

        Parameters
        ----------
        newstate: State
            The FSM will switch to this state.

        Note: Both the current and new states must be valid, otherwise nothing
        will happen and we'll stay in the current state.
        """
        if self.cur_state and newstate:
            self.pre_state = self.cur_state
            self.cur_state.leave(self.owner)
            self.cur_state = newstate
            self.cur_state.enter(self.owner)

    def revert_state(self):
        """Reverts owner to its previous state; useful for state blips."""
        self.change_state(self.pre_state)

    def handle_msg(self, message):
        """Used by the FSM to route received messages.

        The message is first passed to the current state, which tries to
        handle it. If the current state fails to do so, the message is then
        passed to the global state, if one exists.

        Parameters
        ----------
        message: tuple
            A message constructed using the telegram() function.

        Returns
        -------
        bool
            True if the message was handled by either the current or global
            state; False otherwise.
        """
        # First let the current state try to handle this message
        if self.cur_state and self.cur_state.on_msg(self.owner, message):
            return True
        # If the above fails, forward this message to the global state
        if self.glo_state and self.glo_state.on_msg(self.owner, message):
            return True
        # If neither, the message could not be handled
        else:
            return False
