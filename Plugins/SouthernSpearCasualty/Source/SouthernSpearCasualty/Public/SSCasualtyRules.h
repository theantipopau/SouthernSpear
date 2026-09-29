// Copyright Southern Spear. All Rights Reserved.

#pragma once

// Engine-free on purpose (ADR-040): only the C++ standard library, so every rule is checked
// outside Unreal as well as in the automation suite (Tools/Casualty/check_casualty_rules.py
// compiles Private/Tests/SSCasualtyRuleChecks.h with g++; SSCasualtyTests.cpp runs the same checks).

#include <algorithm>

/**
 * Casualty care (ADR-040, GDD §4.3). Pure rules: no world, no clock beyond what the caller passes.
 * The server owns every transition; the runtime component calls these and replicates the result.
 *
 *   Up (maybe bleeding) --lethal hit or bled out--> Downed --bleed-out timer--> Dead
 *   Up --lethal head hit--> Dead          Downed --any hit ("finished")--> Dead
 *   Downed --stabilised by a teammate or medic--> Up
 *
 * Health only ever rises through a completed treatment. Tick() never raises it (IC-11).
 */
namespace SSCasualty
{
	enum class EState : unsigned char { Up, Downed, Dead };
	enum class EZone : unsigned char { Head, Torso, Arm, Leg };
	/** Who is doing the treating, relative to the patient. A medic treating themselves is Self. */
	enum class ETreater : unsigned char { Self, Teammate, Medic };
	enum class EAction : unsigned char
	{
		Dressing,     // stops bleeding; no health (self or teammate; a medic counts as a teammate)
		Stabilise,    // a downed soldier back up (teammate or medic)
		Treat,        // stops bleeding and restores health (medic only)
		KitSelfTreat, // treat yourself at a medic's kit (self only, costs a kit charge)
	};

	/** Every number the design sets. The runtime fills this from USSCasualtySettings (DefaultGame.ini). */
	struct FTuning
	{
		float MaxHealth = 100.f;

		// Damage multiplier per zone (IC-08). A lethal head hit kills outright instead of downing.
		float HeadMultiplier = 4.0f;
		float TorsoMultiplier = 1.0f;
		float ArmMultiplier = 0.6f;
		float LegMultiplier = 0.7f;

		// Bleed added per point of damage taken (health per second), per zone. Limbs bleed more.
		float HeadBleedPerDamage = 0.0f;
		float TorsoBleedPerDamage = 0.02f;
		float ArmBleedPerDamage = 0.04f;
		float LegBleedPerDamage = 0.04f;
		float MaxBleed = 4.0f;

		float BleedOutSeconds = 45.f;

		float DressingSelfSeconds = 6.f;
		float DressingTeammateSeconds = 4.f;
		float StabiliseTeammateSeconds = 8.f;
		float StabiliseMedicSeconds = 5.f;
		float TreatMedicSeconds = 5.f;
		float KitSelfTreatSeconds = 8.f;

		float StabiliseTeammateHealth = 25.f;
		float StabiliseTeammateBleed = 0.3f; // "still bleeding lightly"
		float StabiliseMedicHealth = 50.f;
		float TreatMedicHealth = 75.f;
		float KitSelfTreatHealth = 60.f;

		int DressingsCarried = 2;
		int MedicDressingsCarried = 6;

		int KitCharges = 8;
		float KitLifetimeSeconds = 180.f;
		float KitRadiusCm = 200.f;
	};

	/** One soldier's casualty state. Replicated by the runtime component. */
	struct FCasualty
	{
		EState State = EState::Up;
		float Health = 100.f;
		float Bleed = 0.f;              // health lost per second while Up
		float BleedOutRemaining = 0.f;  // seconds left while Downed
		int Dressings = 2;

		bool IsBleeding() const { return State == EState::Up && Bleed > 0.f; }
	};

	/** A medic's dropped kit. */
	struct FKit
	{
		int Charges = 8;
		float Age = 0.f;
	};

	enum class ETransition : unsigned char { None, Downed, Died };

	struct FHitOutcome
	{
		float Applied = 0.f;  // health actually removed
		ETransition Transition = ETransition::None;
	};

	inline FCasualty MakeSoldier(const FTuning& T, bool bMedic)
	{
		FCasualty C;
		C.Health = T.MaxHealth;
		C.Dressings = bMedic ? T.MedicDressingsCarried : T.DressingsCarried;
		return C;
	}

	inline FKit MakeKit(const FTuning& T)
	{
		FKit K;
		K.Charges = T.KitCharges;
		return K;
	}

	inline float Multiplier(const FTuning& T, EZone Zone)
	{
		switch (Zone)
		{
		case EZone::Head: return T.HeadMultiplier;
		case EZone::Arm: return T.ArmMultiplier;
		case EZone::Leg: return T.LegMultiplier;
		default: return T.TorsoMultiplier;
		}
	}

	inline float BleedPerDamage(const FTuning& T, EZone Zone)
	{
		switch (Zone)
		{
		case EZone::Head: return T.HeadBleedPerDamage;
		case EZone::Arm: return T.ArmBleedPerDamage;
		case EZone::Leg: return T.LegBleedPerDamage;
		default: return T.TorsoBleedPerDamage;
		}
	}

	inline void GoDown(FCasualty& C, const FTuning& T)
	{
		C.State = EState::Downed;
		C.Health = 0.f;
		C.Bleed = 0.f;
		C.BleedOutRemaining = T.BleedOutSeconds;
	}

	inline void Die(FCasualty& C)
	{
		C.State = EState::Dead;
		C.Health = 0.f;
		C.Bleed = 0.f;
		C.BleedOutRemaining = 0.f;
	}

	/** A hit of RawDamage (before the zone multiplier). Server only. */
	inline FHitOutcome ApplyHit(FCasualty& C, const FTuning& T, EZone Zone, float RawDamage)
	{
		FHitOutcome Out;
		if (C.State == EState::Dead || !(RawDamage > 0.f))
		{
			return Out;
		}
		if (C.State == EState::Downed)
		{
			Die(C); // finished
			Out.Transition = ETransition::Died;
			return Out;
		}
		const float Damage = RawDamage * Multiplier(T, Zone);
		if (Damage >= C.Health)
		{
			Out.Applied = C.Health;
			if (Zone == EZone::Head)
			{
				Die(C);
				Out.Transition = ETransition::Died;
			}
			else
			{
				GoDown(C, T);
				Out.Transition = ETransition::Downed;
			}
			return Out;
		}
		C.Health -= Damage;
		C.Bleed = std::min(T.MaxBleed, C.Bleed + Damage * BleedPerDamage(T, Zone));
		Out.Applied = Damage;
		return Out;
	}

	/** Time passing. Bleeding drains health; a downed soldier's timer runs. Never raises health. */
	inline ETransition Tick(FCasualty& C, const FTuning& T, float DeltaSeconds)
	{
		if (!(DeltaSeconds > 0.f))
		{
			return ETransition::None;
		}
		if (C.State == EState::Up && C.Bleed > 0.f)
		{
			C.Health -= C.Bleed * DeltaSeconds;
			if (C.Health <= 0.f)
			{
				GoDown(C, T);
				return ETransition::Downed;
			}
		}
		else if (C.State == EState::Downed)
		{
			C.BleedOutRemaining -= DeltaSeconds;
			if (C.BleedOutRemaining <= 0.f)
			{
				Die(C);
				return ETransition::Died;
			}
		}
		return ETransition::None;
	}

	/** How long an action takes, or a negative number when that treater may not do it. */
	inline float ActionSeconds(const FTuning& T, EAction Action, ETreater Treater)
	{
		switch (Action)
		{
		case EAction::Dressing:
			return Treater == ETreater::Self ? T.DressingSelfSeconds : T.DressingTeammateSeconds;
		case EAction::Stabilise:
			if (Treater == ETreater::Medic) return T.StabiliseMedicSeconds;
			if (Treater == ETreater::Teammate) return T.StabiliseTeammateSeconds;
			return -1.f; // nobody picks themselves up
		case EAction::Treat:
			return Treater == ETreater::Medic ? T.TreatMedicSeconds : -1.f;
		case EAction::KitSelfTreat:
			return Treater == ETreater::Self ? T.KitSelfTreatSeconds : -1.f;
		}
		return -1.f;
	}

	inline bool KitUsable(const FKit& Kit, const FTuning& T)
	{
		return Kit.Charges > 0 && Kit.Age < T.KitLifetimeSeconds;
	}

	/**
	 * Whether Action may start now. `TreaterDressings` is the dressings the one applying a Dressing
	 * holds (the patient's own when Self). `Kit` is the kit in range, or null.
	 */
	inline bool CanStart(const FCasualty& Patient, const FTuning& T, EAction Action, ETreater Treater,
		int TreaterDressings, const FKit* Kit)
	{
		if (ActionSeconds(T, Action, Treater) < 0.f)
		{
			return false;
		}
		switch (Action)
		{
		case EAction::Dressing:
			return Patient.IsBleeding() && TreaterDressings > 0;
		case EAction::Stabilise:
			return Patient.State == EState::Downed;
		case EAction::Treat:
			return Patient.State == EState::Up && (Patient.Bleed > 0.f || Patient.Health < T.TreatMedicHealth);
		case EAction::KitSelfTreat:
			return Patient.State == EState::Up && Kit && KitUsable(*Kit, T)
				&& (Patient.Bleed > 0.f || Patient.Health < T.KitSelfTreatHealth);
		}
		return false;
	}

	/**
	 * The result of a completed action (the runtime times it and cancels it on movement or damage).
	 * Treatment never lowers health. Returns false, changing nothing, when the action could not start.
	 */
	inline bool Complete(FCasualty& Patient, const FTuning& T, EAction Action, ETreater Treater,
		int& TreaterDressings, FKit* Kit)
	{
		if (!CanStart(Patient, T, Action, Treater, TreaterDressings, Kit))
		{
			return false;
		}
		switch (Action)
		{
		case EAction::Dressing:
			Patient.Bleed = 0.f;
			--TreaterDressings;
			break;
		case EAction::Stabilise:
			Patient.State = EState::Up;
			Patient.BleedOutRemaining = 0.f;
			if (Treater == ETreater::Medic)
			{
				Patient.Health = T.StabiliseMedicHealth;
				Patient.Bleed = 0.f;
			}
			else
			{
				Patient.Health = T.StabiliseTeammateHealth;
				Patient.Bleed = T.StabiliseTeammateBleed;
			}
			break;
		case EAction::Treat:
			Patient.Bleed = 0.f;
			Patient.Health = std::max(Patient.Health, T.TreatMedicHealth);
			break;
		case EAction::KitSelfTreat:
			Patient.Bleed = 0.f;
			Patient.Health = std::max(Patient.Health, T.KitSelfTreatHealth);
			--Kit->Charges;
			break;
		}
		return true;
	}

	/** Take one dressing from a kit in range, up to the carry limit. */
	inline bool TakeDressingFromKit(FCasualty& Soldier, FKit& Kit, const FTuning& T, bool bMedic)
	{
		const int Limit = bMedic ? T.MedicDressingsCarried : T.DressingsCarried;
		if (Soldier.State != EState::Up || Soldier.Dressings >= Limit || !KitUsable(Kit, T))
		{
			return false;
		}
		++Soldier.Dressings;
		--Kit.Charges;
		return true;
	}

	/** Age a kit. False once it has expired or run out, when the runtime removes it. */
	inline bool TickKit(FKit& Kit, const FTuning& T, float DeltaSeconds)
	{
		Kit.Age += std::max(0.f, DeltaSeconds);
		return KitUsable(Kit, T);
	}
}
