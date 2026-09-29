// Copyright Southern Spear. All Rights Reserved.

#pragma once

// The casualty rule checks (ADR-040), engine-free so the same checks run in the automation suite
// (SSCasualtyTests.cpp) and outside Unreal (Tools/Casualty/check_casualty_rules.py, g++).
// Each group adds a message to Failures for every check that does not hold.

#include "SSCasualtyRules.h"

#include <cmath>
#include <string>
#include <vector>

namespace SSCasualtyChecks
{
	using namespace SSCasualty;

	struct FReport
	{
		std::vector<std::string> Failures;
		int Checks = 0;

		void Check(bool bOk, const std::string& What)
		{
			++Checks;
			if (!bOk)
			{
				Failures.push_back(What);
			}
		}
	};

	inline bool Near(float A, float B, float Tolerance = 1e-3f)
	{
		return std::fabs(A - B) <= Tolerance;
	}

	/** IC-08: zones scale damage; limbs bleed more than the torso; a lethal head hit kills, others down. */
	inline void Zones(FReport& R)
	{
		const FTuning T;
		FCasualty Torso = MakeSoldier(T, false);
		ApplyHit(Torso, T, EZone::Torso, 30.f);
		R.Check(Near(Torso.Health, 70.f), "torso hit removes 30 of 30");
		FCasualty Arm = MakeSoldier(T, false);
		ApplyHit(Arm, T, EZone::Arm, 30.f);
		R.Check(Near(Arm.Health, 82.f), "arm hit removes 30 x 0.6 = 18");
		FCasualty Leg = MakeSoldier(T, false);
		ApplyHit(Leg, T, EZone::Leg, 30.f);
		R.Check(Near(Leg.Health, 79.f), "leg hit removes 30 x 0.7 = 21");
		R.Check(Torso.IsBleeding() && Arm.IsBleeding() && Leg.IsBleeding(), "body and limb hits bleed");
		R.Check(Arm.Bleed / 18.f > Torso.Bleed / 30.f, "an arm bleeds more per point of damage than the torso");

		FCasualty Head = MakeSoldier(T, false);
		const FHitOutcome HeadHit = ApplyHit(Head, T, EZone::Head, 30.f);
		R.Check(HeadHit.Transition == ETransition::Died && Head.State == EState::Dead, "a 30-damage head hit (x4 = 120) kills outright");

		FCasualty Graze = MakeSoldier(T, false);
		ApplyHit(Graze, T, EZone::Head, 5.f);
		R.Check(Graze.State == EState::Up && Near(Graze.Health, 80.f), "a non-lethal head graze wounds, it does not kill");

		FCasualty Chest = MakeSoldier(T, false);
		const FHitOutcome Lethal = ApplyHit(Chest, T, EZone::Torso, 150.f);
		R.Check(Lethal.Transition == ETransition::Downed && Chest.State == EState::Downed, "a lethal torso hit downs, it does not kill");
		R.Check(Near(Chest.BleedOutRemaining, T.BleedOutSeconds), "the bleed-out timer starts full");
		R.Check(Near(Lethal.Applied, 100.f), "a lethal hit applies only the health that was left");

		FCasualty Capped = MakeSoldier(T, false);
		for (int I = 0; I < 5; ++I) ApplyHit(Capped, T, EZone::Leg, 20.f);
		R.Check(Capped.Bleed <= T.MaxBleed, "bleed is capped");

		FCasualty Zero = MakeSoldier(T, false);
		ApplyHit(Zero, T, EZone::Torso, 0.f);
		ApplyHit(Zero, T, EZone::Torso, -10.f);
		R.Check(Near(Zero.Health, 100.f) && !Zero.IsBleeding(), "zero or negative damage does nothing");
	}

	/** Downed and dead: the timer, being finished, and nothing touching the dead. */
	inline void States(FReport& R)
	{
		const FTuning T;
		FCasualty C = MakeSoldier(T, false);
		ApplyHit(C, T, EZone::Torso, 200.f);
		R.Check(Tick(C, T, T.BleedOutSeconds - 1.f) == ETransition::None && C.State == EState::Downed, "still downed a second before bleed-out");
		R.Check(Tick(C, T, 2.f) == ETransition::Died && C.State == EState::Dead, "dies when the bleed-out timer runs out");

		FCasualty Finished = MakeSoldier(T, false);
		ApplyHit(Finished, T, EZone::Torso, 200.f);
		R.Check(ApplyHit(Finished, T, EZone::Leg, 1.f).Transition == ETransition::Died, "any hit on a downed soldier finishes them");

		FCasualty Dead = MakeSoldier(T, false);
		ApplyHit(Dead, T, EZone::Head, 100.f);
		R.Check(ApplyHit(Dead, T, EZone::Torso, 50.f).Transition == ETransition::None, "hits on the dead do nothing");
		R.Check(Tick(Dead, T, 10.f) == ETransition::None, "time does nothing to the dead");
		int Dressings = 2;
		R.Check(!Complete(Dead, T, EAction::Stabilise, ETreater::Medic, Dressings, nullptr), "the dead cannot be stabilised");

		FCasualty Bleeder = MakeSoldier(T, false);
		ApplyHit(Bleeder, T, EZone::Leg, 100.f); // 70 damage, bleeding 2.8/s
		float Seconds = 0.f;
		while (Bleeder.State == EState::Up && Seconds < 60.f)
		{
			Tick(Bleeder, T, 0.1f);
			Seconds += 0.1f;
		}
		R.Check(Bleeder.State == EState::Downed, "an untreated leg wound bleeds a soldier down");
		R.Check(Seconds > 9.f && Seconds < 12.f, "30 health at 2.8/s goes down after about 10.7 s");
	}

	/** Every treatment row in ADR-040, and who may do what. */
	inline void Treatment(FReport& R)
	{
		const FTuning T;
		int Mine = 2;

		FCasualty SelfDressed = MakeSoldier(T, false);
		ApplyHit(SelfDressed, T, EZone::Arm, 30.f);
		const float Before = SelfDressed.Health;
		R.Check(Complete(SelfDressed, T, EAction::Dressing, ETreater::Self, Mine, nullptr), "a bleeding soldier can dress themselves");
		R.Check(!SelfDressed.IsBleeding() && Near(SelfDressed.Health, Before) && Mine == 1, "a dressing stops bleeding, returns no health, uses one");
		R.Check(!CanStart(SelfDressed, T, EAction::Dressing, ETreater::Self, Mine, nullptr), "no dressing on a wound that isn't bleeding");
		int None = 0;
		FCasualty Bleeding = MakeSoldier(T, false);
		ApplyHit(Bleeding, T, EZone::Arm, 30.f);
		R.Check(!CanStart(Bleeding, T, EAction::Dressing, ETreater::Self, None, nullptr), "no dressing without one to apply");

		FCasualty Down = MakeSoldier(T, false);
		ApplyHit(Down, T, EZone::Torso, 200.f);
		R.Check(!CanStart(Down, T, EAction::Stabilise, ETreater::Self, Mine, nullptr), "nobody stabilises themselves");
		FCasualty ByMate = Down;
		R.Check(Complete(ByMate, T, EAction::Stabilise, ETreater::Teammate, Mine, nullptr), "a teammate stabilises");
		R.Check(ByMate.State == EState::Up && Near(ByMate.Health, 25.f) && ByMate.IsBleeding(), "teammate: up at 25, still bleeding lightly");
		FCasualty ByMedic = Down;
		Complete(ByMedic, T, EAction::Stabilise, ETreater::Medic, Mine, nullptr);
		R.Check(ByMedic.State == EState::Up && Near(ByMedic.Health, 50.f) && !ByMedic.IsBleeding(), "medic: up at 50, bleeding stopped");

		FCasualty Wounded = MakeSoldier(T, false);
		ApplyHit(Wounded, T, EZone::Torso, 60.f);
		R.Check(!CanStart(Wounded, T, EAction::Treat, ETreater::Teammate, Mine, nullptr), "only a medic treats");
		R.Check(Complete(Wounded, T, EAction::Treat, ETreater::Medic, Mine, nullptr) && Near(Wounded.Health, 75.f) && !Wounded.IsBleeding(), "medic treatment: 75 health, bleeding stopped");
		FCasualty Healthy = MakeSoldier(T, false);
		R.Check(!CanStart(Healthy, T, EAction::Treat, ETreater::Medic, Mine, nullptr), "nothing to treat on a healthy soldier");
		FCasualty Scratched = MakeSoldier(T, false);
		ApplyHit(Scratched, T, EZone::Arm, 10.f); // 94 health, bleeding
		R.Check(Complete(Scratched, T, EAction::Treat, ETreater::Medic, Mine, nullptr) && Near(Scratched.Health, 94.f) && !Scratched.IsBleeding(), "treatment above 75 stops the bleed and never lowers health");

		R.Check(ActionSeconds(T, EAction::Dressing, ETreater::Self) == 6.f && ActionSeconds(T, EAction::Dressing, ETreater::Teammate) == 4.f, "dressing: 6 s self, 4 s teammate");
		R.Check(ActionSeconds(T, EAction::Stabilise, ETreater::Teammate) == 8.f && ActionSeconds(T, EAction::Stabilise, ETreater::Medic) == 5.f, "stabilise: 8 s teammate, 5 s medic");
		R.Check(ActionSeconds(T, EAction::KitSelfTreat, ETreater::Medic) < 0.f, "the kit's self-treatment is only for yourself");
	}

	/** GDD §4.3: self-treatment is strictly worse than being treated. */
	inline void SelfIsWorse(FReport& R)
	{
		const FTuning T;
		R.Check(T.DressingSelfSeconds > T.DressingTeammateSeconds, "dressing yourself is slower than being dressed");
		R.Check(T.StabiliseMedicSeconds < T.StabiliseTeammateSeconds && T.StabiliseMedicHealth > T.StabiliseTeammateHealth, "a medic stabilises faster and to a better outcome");
		R.Check(T.KitSelfTreatHealth < T.TreatMedicHealth && T.KitSelfTreatSeconds > T.TreatMedicSeconds, "treating yourself at a kit is worse than a medic's treatment");
		R.Check(T.MedicDressingsCarried > T.DressingsCarried, "medics carry more dressings");
	}

	/** The medic's kit: charges, lifetime, range of use, carry limits. */
	inline void Kit(FReport& R)
	{
		const FTuning T;
		FKit K = MakeKit(T);
		FCasualty Soldier = MakeSoldier(T, false);
		Soldier.Dressings = 0;
		R.Check(TakeDressingFromKit(Soldier, K, T, false) && Soldier.Dressings == 1 && K.Charges == 7, "take a dressing: one charge");
		TakeDressingFromKit(Soldier, K, T, false);
		R.Check(!TakeDressingFromKit(Soldier, K, T, false) && Soldier.Dressings == 2 && K.Charges == 6, "not beyond the carry limit of 2");
		FCasualty Medic = MakeSoldier(T, true);
		R.Check(Medic.Dressings == 6 && !TakeDressingFromKit(Medic, K, T, true), "a medic starts with 6, the limit");

		FCasualty Hurt = MakeSoldier(T, false);
		ApplyHit(Hurt, T, EZone::Torso, 50.f);
		int Mine = 2;
		R.Check(!CanStart(Hurt, T, EAction::KitSelfTreat, ETreater::Self, Mine, nullptr), "no kit, no kit treatment");
		R.Check(Complete(Hurt, T, EAction::KitSelfTreat, ETreater::Self, Mine, &K) && Near(Hurt.Health, 60.f) && !Hurt.IsBleeding() && K.Charges == 5, "kit self-treatment: 60 health, bleeding stopped, one charge");
		R.Check(!CanStart(Hurt, T, EAction::KitSelfTreat, ETreater::Self, Mine, &K), "nothing more from the kit at 60 health and no bleed");

		FKit Empty = MakeKit(T);
		Empty.Charges = 0;
		FCasualty Other = MakeSoldier(T, false);
		ApplyHit(Other, T, EZone::Torso, 50.f);
		R.Check(!CanStart(Other, T, EAction::KitSelfTreat, ETreater::Self, Mine, &Empty), "an empty kit does nothing");

		FKit Old = MakeKit(T);
		R.Check(TickKit(Old, T, T.KitLifetimeSeconds - 1.f), "a kit lasts its lifetime");
		R.Check(!TickKit(Old, T, 2.f) && !CanStart(Other, T, EAction::KitSelfTreat, ETreater::Self, Mine, &Old), "and then expires");
	}

	/** IC-11: health never rises without a treatment, with or without a kit nearby. */
	inline void NoRegeneration(FReport& R)
	{
		const FTuning T;
		for (int Case = 0; Case < 3; ++Case)
		{
			FCasualty C = MakeSoldier(T, false);
			ApplyHit(C, T, EZone::Torso, 40.f);
			int Mine = 2;
			if (Case >= 1)
			{
				Complete(C, T, EAction::Dressing, ETreater::Self, Mine, nullptr); // dressed: bleeding stopped
			}
			FKit Nearby = MakeKit(T); // Case 2: a kit in range the whole time, unused
			float Previous = C.Health;
			bool bRose = false;
			for (int Step = 0; Step < 1200; ++Step) // 120 s at 10 Hz
			{
				Tick(C, T, 0.1f);
				if (Case == 2) TickKit(Nearby, T, 0.1f);
				bRose |= C.Health > Previous + 1e-6f;
				Previous = C.Health;
			}
			R.Check(!bRose, Case == 0 ? "health never rises while bleeding" : Case == 1 ? "health never rises once dressed" : "health never rises beside an unused kit");
			if (Case >= 1)
			{
				R.Check(Near(C.Health, 60.f), "a dressed soldier stays where the dressing left them");
			}
		}
	}

	inline FReport RunAll()
	{
		FReport R;
		Zones(R);
		States(R);
		Treatment(R);
		SelfIsWorse(R);
		Kit(R);
		NoRegeneration(R);
		return R;
	}
}
